from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
from PyQt5.QtCore import QObject

# Generic types for static type checking across derived controllers
ViewType = TypeVar("ViewType")
ModelType = TypeVar("ModelType")


class BaseController(QObject, ABC, Generic[ViewType, ModelType]):
    """
    Abstract Base Class for MVC Controllers in PyQt.

    Provides lifecycle hooks for signal binding, view management,
    and cleanup operations.
    """

    def __init__(
            self,
            view: ViewType,
            model: Optional[ModelType] = None,
            parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.view: ViewType = view
        self.model: Optional[ModelType] = model

        # Enforce signal connections on instantiation
        self._connect_signals()

    @abstractmethod
    def _connect_signals(self) -> None:
        """
        Abstract method. Derived classes must connect PyQt signals
        from self.view to controller handler slots here.
        """
        pass

    def show_view(self) -> None:
        """Displays the attached view widget."""

        if hasattr(self.view, "show"):
            self.view.show()

    def hide_view(self) -> None:
        """Hides the attached view widget."""
        if hasattr(self.view, "hide"):
            self.view.hide()

    def cleanup(self) -> None:
        """
        Override in subclasses to disconnect signals, terminate worker threads,
        or release memory when switching views.
        """
        pass