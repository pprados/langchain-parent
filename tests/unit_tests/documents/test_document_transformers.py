from typing import Any, AsyncIterator, Iterator, Sequence

import pytest
from langchain_core.documents import Document

from langchain_rag.document_transformers import DocumentTransformers
from langchain_rag.document_transformers.lazy_document_transformer import (
    LazyDocumentTransformer,
)

from .sample_transformer import (
    LowerLazyTransformer,
    UpperLazyTransformer,
)


def by_pg(doc: Document) -> str:
    return doc.page_content


class _SplitWords(LazyDocumentTransformer):
    def lazy_transform_documents(
        self, documents: Iterator[Document], **kwargs: Any
    ) -> Iterator[Document]:
        for doc in documents:
            for text in doc.page_content.split(" "):
                yield Document(page_content=text, metadata=doc.metadata)

    async def _alazy_transform_documents(  # type: ignore
        self, documents: AsyncIterator[Document], **kwargs: Any
    ) -> AsyncIterator[Document]:
        async for doc in documents:
            for text in doc.page_content.split(" "):
                yield Document(page_content=text, metadata=doc.metadata)


@pytest.mark.parametrize(
    "transformers",
    [
        [
            _SplitWords(),
            UpperLazyTransformer(),
        ]
    ],
)
def test_document_transformers_legacy(transformers: Sequence) -> None:
    doc1 = Document(page_content="my test")
    doc2 = Document(page_content="other test")

    transformer = DocumentTransformers(transformers=transformers)
    r = transformer.transform_documents([doc1, doc2])
    assert len(r) == 6
    assert sorted(r, key=by_pg) == sorted(
        [
            Document(page_content="my"),
            Document(page_content="test"),
            Document(page_content=doc1.page_content.upper()),
            Document(page_content="other"),
            Document(page_content="test"),
            Document(page_content=doc2.page_content.upper()),
        ],
        key=by_pg,
    )


@pytest.mark.parametrize(
    "transformers", [[UpperLazyTransformer(), LowerLazyTransformer()]]
)
def test_transform_documents(transformers: Sequence) -> None:
    doc1 = Document(page_content="my test")
    doc2 = Document(page_content="other test")
    transformer = DocumentTransformers(transformers=transformers)
    r = transformer.transform_documents([doc1, doc2])
    assert len(r) == 4
    assert sorted(r, key=by_pg) == sorted(
        [
            Document(page_content=doc1.page_content.upper()),
            Document(page_content=doc1.page_content.lower()),
            Document(page_content=doc2.page_content.upper()),
            Document(page_content=doc2.page_content.lower()),
        ],
        key=by_pg,
    )


@pytest.mark.parametrize(
    "transformers", [[UpperLazyTransformer(), LowerLazyTransformer()]]
)
@pytest.mark.asyncio
async def test_atransform_documents(transformers: Sequence) -> None:
    doc1 = Document(page_content="my test")
    doc2 = Document(page_content="other test")
    transformer = DocumentTransformers(transformers=transformers)
    r = await transformer.atransform_documents([doc1, doc2])
    assert len(r) == 4
    assert sorted(r, key=by_pg) == sorted(
        [
            Document(page_content=doc1.page_content.upper()),
            Document(page_content=doc2.page_content.upper()),
            Document(page_content=doc1.page_content.lower()),
            Document(page_content=doc2.page_content.lower()),
        ],
        key=by_pg,
    )


@pytest.mark.parametrize(
    "transformers", [[UpperLazyTransformer(), LowerLazyTransformer()]]
)
def test_lazy_transform_documents(transformers: Sequence) -> None:
    doc1 = Document(page_content="my test")
    doc2 = Document(page_content="other test")
    transformer = DocumentTransformers(transformers=transformers)
    r = [doc for doc in transformer.lazy_transform_documents(iter([doc1, doc2]))]
    assert len(r) == 4

    assert sorted(r, key=by_pg) == sorted(
        [
            Document(page_content=doc1.page_content.upper()),
            Document(page_content=doc2.page_content.upper()),
            Document(page_content=doc1.page_content.lower()),
            Document(page_content=doc2.page_content.lower()),
        ],
        key=by_pg,
    )


@pytest.mark.parametrize(
    "transformers", [[UpperLazyTransformer(), LowerLazyTransformer()]]
)
@pytest.mark.asyncio
async def test_alazy_transform_documents(transformers: Sequence) -> None:
    doc1 = Document(page_content="my test")
    doc2 = Document(page_content="other test")
    transformer = DocumentTransformers(transformers=transformers)
    r = [doc async for doc in transformer.alazy_transform_documents(iter([doc1, doc2]))]
    assert len(r) == 4
    assert sorted(r, key=by_pg) == sorted(
        [
            Document(page_content=doc1.page_content.upper()),
            Document(page_content=doc2.page_content.upper()),
            Document(page_content=doc1.page_content.lower()),
            Document(page_content=doc2.page_content.lower()),
        ],
        key=by_pg,
    )
