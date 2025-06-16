import os
import threading


class Singleton(type):
    """metaclass Singleton pattern
    https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            pid = os.getpid()
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
            print(f"process({pid}) init singleton for {cls}")
        return cls._instances[cls]


class ThreadSingleton(type):
    """Keep the singleton for each thread
    Notice that the singleton for each will NOT release after use.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        thread_id = threading.current_thread().ident
        pid = os.getpid()
        id_key = (thread_id, pid)
        cls._instances.setdefault(cls, {})
        if id_key not in cls._instances[cls]:
            cls._instances[cls][id_key] = super(ThreadSingleton, cls).__call__(
                *args, **kwargs
            )
            print(f"init thread singleton for {cls}: {id_key}")
        return cls._instances[cls][id_key]


class ProcessSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        pid = os.getpid()
        cls._instances.setdefault(cls, {})
        if pid not in cls._instances[cls]:
            cls._instances[cls][pid] = super(ProcessSingleton, cls).__call__(
                *args, **kwargs
            )
            print(f"process({pid}) init process singleton for {cls}")
        return cls._instances[cls][pid]
