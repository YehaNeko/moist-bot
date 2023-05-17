from typing import Any, Dict, List, Optional, TypeVar

import aiofiles
import asyncio
import orjson

_T = TypeVar('_T', bound=Dict[str, Any])


class AsyncJsonDB:
    """An async database handler based on ``json`` internally.

    Not designed to hold a large amount of data.
    Mostly meant for saving cache to file.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lock = asyncio.Lock()
        self.queue = asyncio.Queue()
        self.execute = asyncio.get_running_loop().run_in_executor

        # Start the queue processing task
        self.worker =  asyncio.create_task(self.process_queue())

        # Cache latest db to avoid unnecessary re-acquirement
        self.data: Dict[str, Any] = await self.read_data()

        # Keep track of when the db has to re-acquire itself from file
        self.db_changed: bool = True  # TODO: Handle states


    async def get(self, key: str) -> Optional[_T]:
        return await self.execute_operation(self._get, key)

    async def set(self, key: str, value: Any) -> None:
        await self.execute_operation(self._set, key, value)

    async def keys(self) -> List[str]:
        return await self.execute_operation(self._keys)

    async def delete(self, key: str) -> None:
        await self.execute_operation(self._delete, key)

    async def clear(self) -> None:
        await self.execute_operation(self._clear)

    async def execute_operation(self, operation, *args) -> Any:
        future = asyncio.Future()
        await self.queue.put((operation, args, future))
        return await future

    async def process_queue(self) -> None:
        while True:
            operation, args, future = await self.queue.get()
            try:
                # Execute the operation and set the future result
                result = await operation(*args)
                future.set_result(result)
            except Exception as e:
                # Set the future exception
                future.set_exception(e)
            finally:
                # Notify the queue that the operation is complete
                self.queue.task_done()
    async def read_data(self) -> _T:
        async with self.lock:
            try:
                async with aiofiles.open(self.filepath, 'r') as f:
                    data = orjson.loads(await f.read())
            except FileNotFoundError:
                data = {}
        return data

    async def write_data(self, data: _T) -> None:
        async with self.lock:
            async with aiofiles.open(self.filepath, 'wb') as f:
                await f.write(await self.execute(None, orjson.dumps, data))

    async def _resolve_data(self, data: Optional[_T]) -> _T:
        """Read data from file if no data is present"""
        if not data:
            return await self.read_data()
        return data

    async def _get(self, key: str, data: Optional[_T] = None) -> Optional[Any]:
        data = await self._resolve_data(data)
        return data.get(key)

    async def _set(self, key: str, value: Any, data: Optional[_T]) -> None:
        data = await self._resolve_data(data)
        data[key] = value
        await self.write_data(data)

    async def _delete(self, key: str, data: Optional[_T]) -> None:
        data = await self._resolve_data(data)
        data.pop(key, None)
        await self.write_data(data)

    async def _keys(self, data: Optional[_T]) -> List[str]:
        data = await self._resolve_data(data)
        return list(data.keys())

    async def _clear(self) -> None:
        await self.write_data({})

    def __del__(self):
        self.worker.cancel()
