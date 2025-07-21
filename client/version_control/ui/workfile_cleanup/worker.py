from qtpy import QtCore
import typing

class CleanupSignals(QtCore.QObject):
    started = QtCore.Signal(str, int)
    updated = QtCore.Signal(int)
    finished = QtCore.Signal(list, int, int)
    failed = QtCore.Signal(object)


class CleanUpWorker(QtCore.QThread):
    def __init__(
        self,
        funct: typing.Callable,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(kwargs.get("parent"))
        self.fucnt = funct
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        self.fucnt(*self.args, **self.kwargs)
