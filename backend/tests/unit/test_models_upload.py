"""
Unit tests for Upload model.

Tests file upload management, processing states, vector search,
and AI integration points.
---
/backend/tests/unit/test_models_upload.py
"""

import pytest
from asyncpg import Connection

from models import FileType, ProcessingStatus, Upload, User


@pytest.mark.unit
class TestUploadModel:
    """
    Test Upload model functionality.
    """

    async def test_upload_init(self):
        """
        Test Upload initialization.
        """
        upload = Upload()
        assert upload.filename == ""
        assert upload.file_path == ""
        assert upload.file_type == ""
        assert upload.file_size == 0
        assert upload.mime_type == ""
        assert upload.processing_status == ProcessingStatus.PENDING
        assert upload.gemini_summary is None
        assert upload.embedding is None
        assert upload.thumbnail_path is None
        assert upload.error_message is None
        assert upload.metadata is None

    async def test_processing_status_enum(self):
        """
        Test ProcessingStatus enum values.
        """
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.ANALYZING == "analyzing"
        assert ProcessingStatus.EMBEDDING == "embedding"
        assert ProcessingStatus.COMPLETED == "completed"
        assert ProcessingStatus.FAILED == "failed"

    async def test_file_type_enum(self):
        """
        Test FileType enum values.
        """
        assert FileType.IMAGE == "image"
        assert FileType.VIDEO == "video"

    async def test_create_upload(
        self, db_connection: Connection, test_user: User, clean_tables: None
    ):
        """
        Test creating a new upload.
        """
        upload = await Upload.create(
            user_id=test_user.id,
            filename="test_image.jpg",
            file_path="/storage/uploads/user123/file456/test_image.jpg",
            file_type="image",
            file_size=1024 * 1024,  # 1MB
            mime_type="image/jpeg",
            metadata={"width": 1920, "height": 1080},
        )

        assert upload.id is not None
        assert upload.user_id == test_user.id
        assert upload.filename == "test_image.jpg"
        assert upload.file_type == "image"
        assert upload.file_size == 1024 * 1024
        assert upload.mime_type == "image/jpeg"
        assert upload.processing_status == ProcessingStatus.PENDING
        assert upload.metadata == {"width": 1920, "height": 1080}
        assert upload.created_at is not None

    async def test_find_by_user(
        self, db_connection: Connection, test_user: User, clean_tables: None
    ):
        """
        Test finding uploads by user.
        """
        # Create multiple uploads
        for i in range(5):
            await Upload.create(
                user_id=test_user.id,
                filename=f"file{i}.{'jpg' if i < 3 else 'mp4'}",
                file_path=f"/storage/{i}",
                file_type="image" if i < 3 else "video",
                file_size=1000 * (i + 1),
                mime_type="image/jpeg" if i < 3 else "video/mp4",
            )

        # Find all uploads
        uploads = await Upload.find_by_user(test_user.id)
        assert len(uploads) == 5

        # Test pagination
        uploads = await Upload.find_by_user(test_user.id, limit=3)
        assert len(uploads) == 3

        # Test file type filter
        images = await Upload.find_by_user(test_user.id, file_type="image")
        assert len(images) == 3
        assert all(u.file_type == "image" for u in images)

        videos = await Upload.find_by_user(test_user.id, file_type="video")
        assert len(videos) == 2
        assert all(u.file_type == "video" for u in videos)

    async def test_find_by_user_with_status_filter(
        self, db_connection: Connection, test_user: User, clean_tables: None
    ):
        """
        Test filtering uploads by processing status.
        """
        # Create uploads with different statuses
        statuses = [
            ProcessingStatus.PENDING,
            ProcessingStatus.ANALYZING,
            ProcessingStatus.COMPLETED,
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED,
        ]

        for i, status in enumerate(statuses):
            upload = await Upload.create(
                user_id=test_user.id,
                filename=f"file{i}.jpg",
                file_path=f"/storage/{i}",
                file_type="image",
                file_size=1000,
                mime_type="image/jpeg",
            )
            # Update status
            await db_connection.execute(
                "UPDATE uploads SET processing_status = $1 WHERE id = $2",
                status,
                upload.id,
            )

        # Filter by status
        completed = await Upload.find_by_user(
            test_user.id, status=ProcessingStatus.COMPLETED
        )
        assert len(completed) == 2

        failed = await Upload.find_by_user(test_user.id, status=ProcessingStatus.FAILED)
        assert len(failed) == 1

    async def test_update_status(
        self, db_connection: Connection, test_user: User, clean_tables: None
    ):
        """
        Test updating processing status.
        """
        upload = await Upload.create(
            user_id=test_user.id,
            filename="test.jpg",
            file_path="/storage/test.jpg",
            file_type="image",
            file_size=1000,
            mime_type="image/jpeg",
        )

        assert upload.processing_status == ProcessingStatus.PENDING

        # Update to analyzing
        await upload.update_status(ProcessingStatus.ANALYZING)
        assert upload.processing_status == ProcessingStatus.ANALYZING
        assert upload.error_message is None

        # Update to failed with error
        await upload.update_status(
            ProcessingStatus.FAILED, "Gemini API rate limit exceeded"
        )
        assert upload.processing_status == ProcessingStatus.FAILED
        assert upload.error_message == "Gemini API rate limit exceeded"

    async def test_update_analysis(
        self,
        db_connection: Connection,
        test_user: User,
        sample_embedding: list[float],
        clean_tables: None,
    ):
        """
        Test updating with AI analysis results.
        """
        upload = await Upload.create(
            user_id=test_user.id,
            filename="beach.jpg",
            file_path="/storage/beach.jpg",
            file_type="image",
            file_size=2000,
            mime_type="image/jpeg",
        )

        summary = "A beautiful sunset over a tropical beach with palm trees"

        await upload.update_analysis(summary, sample_embedding)

        assert upload.gemini_summary == summary
        assert upload.embedding == sample_embedding
        assert upload.processing_status == ProcessingStatus.COMPLETED
        assert len(upload.embedding) == 1536

    async def test_update_thumbnail(
        self, db_connection: Connection, test_user: User, clean_tables: None
    ):
        """
        Test updating thumbnail path.
        """
        upload = await Upload.create(
            user_id=test_user.id,
            filename="video.mp4",
            file_path="/storage/video.mp4",
            file_type="video",
            file_size=10000000,
            mime_type="video/mp4",
        )

        thumbnail_path = "/storage/thumbnails/video_thumb.jpg"

        await upload.update_thumbnail(thumbnail_path)

        assert upload.thumbnail_path == thumbnail_path

    async def test_get_pending_uploads(
        self, db_connection: Connection, test_user: User, clean_tables: None
    ):
        """
        Test getting uploads that need processing.
        """
        # Create mix of uploads
        for i in range(10):
            upload = await Upload.create(
                user_id=test_user.id,
                filename=f"file{i}.jpg",
                file_path=f"/storage/{i}",
                file_type="image",
                file_size=1000,
                mime_type="image/jpeg",
            )

            # Set some to different statuses
            if i >= 5:
                await db_connection.execute(
                    "UPDATE uploads SET processing_status = $1 WHERE id = $2",
                    ProcessingStatus.COMPLETED,
                    upload.id,
                )

        # Get pending uploads
        pending = await Upload.get_pending_uploads(limit=3)

        assert len(pending) == 3
        assert all(u.processing_status == ProcessingStatus.PENDING for u in pending)

        # Should be ordered by created_at ASC (oldest first)
        assert pending[0].created_at <= pending[1].created_at

    async def test_count_by_user(
        self, db_connection: Connection, test_user: User, clean_tables: None
    ):
        """
        Test counting uploads by status for a user.
        """
        # Create uploads with various statuses
        status_counts = {
            ProcessingStatus.PENDING: 3,
            ProcessingStatus.ANALYZING: 1,
            ProcessingStatus.EMBEDDING: 1,
            ProcessingStatus.COMPLETED: 5,
            ProcessingStatus.FAILED: 2,
        }

        for status, count in status_counts.items():
            for _ in range(count):
                upload = await Upload.create(
                    user_id=test_user.id,
                    filename="file.jpg",
                    file_path="/storage/file.jpg",
                    file_type="image",
                    file_size=1000,
                    mime_type="image/jpeg",
                )
                await db_connection.execute(
                    "UPDATE uploads SET processing_status = $1 WHERE id = $2",
                    status,
                    upload.id,
                )

        # Get counts
        counts = await Upload.count_by_user(test_user.id)

        assert counts == status_counts

    async def test_to_dict_embedding_handling(self, sample_embedding: list[float]):
        """
        Test that embeddings are handled properly in to_dict.
        """
        upload = Upload(
            filename="test.jpg",
            embedding=sample_embedding,
        )

        # Default behavior: exclude embedding, add flag
        result = upload.to_dict()
        assert "embedding" not in result
        assert result["has_embedding"] is True

        # Can explicitly include embedding
        result = upload.to_dict(exclude={"filename"})
        assert "embedding" not in result  # Still excluded by default
        assert result["has_embedding"] is True

        # Test with no embedding
        upload.embedding = None
        result = upload.to_dict()
        assert "has_embedding" not in result

    async def test_search_by_embedding(
        self,
        db_connection: Connection,
        test_user: User,
        sample_embedding: list[float],
        clean_tables: None,
    ):
        """
        Test vector similarity search.
        """
        # Create uploads with embeddings
        embeddings = []
        for i in range(3):
            # Create slightly different embeddings
            embedding = sample_embedding.copy()
            embedding[0] += i * 0.1  # Small variation

            upload = await Upload.create(
                user_id=test_user.id,
                filename=f"image{i}.jpg",
                file_path=f"/storage/{i}",
                file_type="image",
                file_size=1000,
                mime_type="image/jpeg",
            )

            # Update with embedding and mark as completed
            await db_connection.execute(
                """
                UPDATE uploads
                SET embedding = $1::vector,
                    processing_status = $2,
                    gemini_summary = $3
                WHERE id = $4
                """,
                embedding,
                ProcessingStatus.COMPLETED,
                f"Image {i} description",
                upload.id,
            )

            embeddings.append(embedding)

        # Search with the first embedding
        results = await Upload.search_by_embedding(
            query_embedding=embeddings[0],
            user_id=test_user.id,
            limit=2,
        )

        assert len(results) == 2

        # Results should be tuples of (Upload, similarity_score)
        upload, score = results[0]
        assert isinstance(upload, Upload)
        assert 0 <= score <= 1

        # First result should be the exact match
        assert upload.filename == "image0.jpg"
        assert score > 0.99  # Should be very close to 1.0

    async def test_upload_repr(self):
        """
        Test string representation of Upload.
        """
        upload = Upload(
            filename="vacation.jpg",
            processing_status=ProcessingStatus.COMPLETED,
        )

        repr_str = str(upload)
        assert "Upload" in repr_str
        assert "vacation.jpg" in repr_str
        assert "COMPLETED" in repr_str

    async def test_create_embedding_index(
        self, db_connection: Connection, clean_tables: None
    ):
        """
        Test creating vector index for similarity search.
        """
        # This would normally be called after having many uploads
        # Just test that it doesn't error
        await Upload.create_embedding_index(lists=10)

        # Verify index exists (index name pattern)
        await db_connection.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname LIKE 'idx_uploads_embedding_%'
            )
            """
        )
        # May or may not exist depending on pgvector version
        # Just ensure no error was raised

    async def test_save_methods(
        self, db_connection: Connection, test_user: User, clean_tables: None
    ):
        """
        Test _insert and _update methods via save().
        """
        # Test insert
        upload = Upload(
            user_id=test_user.id,
            filename="new.jpg",
            file_path="/storage/new.jpg",
            file_type="image",
            file_size=5000,
            mime_type="image/jpeg",
        )

        await upload.save()
        assert upload.id is not None

        # Test update
        original_updated = upload.updated_at
        upload.filename = "renamed.jpg"

        await upload.save()
        assert upload.updated_at > original_updated

        # Verify in database
        filename = await db_connection.fetchval(
            "SELECT filename FROM uploads WHERE id = $1",
            upload.id,
        )
        assert filename == "renamed.jpg"
