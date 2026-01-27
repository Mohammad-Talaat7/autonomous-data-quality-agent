import airbyte as _ab
from typing import Dict, Any


class AirByteSource:
    def __init__(self, source: Any) -> None:
        self._source = source

    def __getattr__(self, name: str) -> Any:
        return getattr(self._source, name)

    def read(self) -> Dict[str, Any]:
        result = self._source.read()
        dfs = {}
        for stream_name, stream_data in result.items():
            df = stream_data.to_pandas()
            # Drop the last 3 columns added by AirByte this start with "_airbyte_"
            if len(df.columns) >= 3 and all(
                c.startswith("_airbyte_") for c in df.columns[-3:]
            ):
                df = df.iloc[:, :-3]
            dfs[stream_name] = df
        return dfs


# Create a module-like object for ab
class ABModule:
    def __getattr__(self, name: str) -> Any:
        return getattr(_ab, name)

    def get_source(self, *args: Any, **kwargs: Any) -> AirByteSource:
        return AirByteSource(_ab.get_source(*args, **kwargs))


ab = ABModule()
