from typing import Mapping

class Monitor:

    def get_data(self) -> Mapping[str, float]:
        raise NotImplementedError

