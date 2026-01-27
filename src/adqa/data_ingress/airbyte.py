import airbyte as _ab


class AirByteSource:
    def __init__(self, source):
        self._source = source

    def __getattr__(self, name):
        return getattr(self._source, name)

    def read(self):
        result = self._source.read()
        dfs = {}
        for stream_name, stream_data in result.items():
            df = stream_data.to_pandas()
            # Drop the last 3 columns added by AirByte
            if len(df.columns) >= 3:
                df = df.iloc[:, :-3]
            dfs[stream_name] = df
        return dfs


# Create a module-like object for ab
class ABModule:
    def __getattr__(self, name):
        return getattr(_ab, name)

    def get_source(self, *args, **kwargs):
        return AirByteSource(_ab.get_source(*args, **kwargs))


ab = ABModule()
