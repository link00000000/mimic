import cProfile
import pstats
from os import PathLike
from typing import Any, Callable, Union


def profile(
    function: Callable,
    text_output_file: Union[str, PathLike[str]] = "mimic.prof.txt",
    profiler_output_file: Union[str, PathLike[str]] = "mimic.prof",
    *args: Any,
    **kwargs: Any
):
    with cProfile.Profile() as prof:
        function(*args, **kwargs)

    with open(text_output_file, 'w') as file:
        stats = pstats.Stats(prof, stream=file)
        stats.sort_stats('time')
        stats.dump_stats(profiler_output_file)
        stats.print_stats()

    print(f"Profile written to {text_output_file} and {profiler_output_file}")
