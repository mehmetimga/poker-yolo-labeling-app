from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|preparing|training|evaluating|done|failed
    model_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)  # path to trained .pt
    base_model: Mapped[str] = mapped_column(String(255), default="yolov8n.pt")

    # Hyperparameters
    epochs: Mapped[int] = mapped_column(Integer, default=100)
    batch_size: Mapped[int] = mapped_column(Integer, default=16)
    img_size: Mapped[int] = mapped_column(Integer, default=640)
    learning_rate: Mapped[float] = mapped_column(Float, default=0.01)

    # Split info
    train_count: Mapped[int] = mapped_column(Integer, default=0)
    val_count: Mapped[int] = mapped_column(Integer, default=0)
    test_count: Mapped[int] = mapped_column(Integer, default=0)
    split_ratio: Mapped[str] = mapped_column(String(32), default="70/20/10")  # train/val/test

    # Metrics (populated after training)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON blob: mAP, loss, per-class AP

    # Evaluation results (populated after evaluation)
    eval_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # per-label accuracy, confusion

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project: Mapped["Project"] = relationship()  # noqa: F821
    splits: Mapped[list["DatasetSplit"]] = relationship(
        back_populates="training_run", cascade="all, delete-orphan"
    )


class DatasetSplit(Base):
    __tablename__ = "dataset_splits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    training_run_id: Mapped[int] = mapped_column(ForeignKey("training_runs.id"), nullable=False)
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id"), nullable=False)
    split: Mapped[str] = mapped_column(String(16), nullable=False)  # train|val|test

    training_run: Mapped["TrainingRun"] = relationship(back_populates="splits")
    image: Mapped["ImageRecord"] = relationship()  # noqa: F821
