import asyncio
import copy
from functools import partial
from typing import Callable, Sequence, Optional, Dict, Any, Generator, cast

from langchain.chains import LLMChain
from langchain.output_parsers import NumberedListOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema import Document, BaseDocumentTransformer
from langchain.schema.language_model import BaseLanguageModel
from langchain_parent.document_transformers import RunnableDocumentTransformer
from langchain_parent.document_transformers.runnable_document_transformer import \
    RunnableGeneratorDocumentTransformer


def _default_get_input(doc: Document) -> Dict[str, Any]:
    """Return the context chain input."""
    return {
        "context": doc.page_content,
    }


_default_template = """
Given a text input, generate {nb_of_questions} questions from it in the same language. 
Context:
```
{context}
```
{format_instructions}"""

_default_parser = NumberedListOutputParser()


def _get_default_chain_prompt() -> PromptTemplate:
    return PromptTemplate.from_template(
        template=_default_template,
        output_parser=_default_parser,
        partial_variables={"format_instructions": _default_parser.get_format_instructions()}
    )


class GenerateQuestions(RunnableGeneratorDocumentTransformer):
    """Generate questions for each Documents."""

    llm_chain: LLMChain
    get_input: Callable[[Document], dict] = _default_get_input
    nb_of_questions: int = 3


    """Callable for constructing the chain input from the query and a Document."""

    def lazy_transform_documents(
            self,
            documents: Sequence[Document],
            **kwargs: Any,
    ) -> Generator[Document, None, None]:
        """Compress page content of raw documents."""
        _callbacks = kwargs.get("callbacks", None)
        for doc in documents:
            _input = {**self.get_input(doc),
                      **{"nb_of_questions": self.nb_of_questions}}
            output = cast(Sequence[str],self.llm_chain.predict_and_parse(
                callbacks=_callbacks,
                **_input))
            if not output:
                continue
            for question in output:
                yield Document(page_content=question, metadata=doc.metadata)

    def transform_documents(
            self,
            documents: Sequence[Document],
            **kwargs: Any
    ) -> Sequence[Document]:
        return list(self.lazy_transform_documents(
            documents=documents,
            **kwargs
        ))

    async def lazy_atransform_documents(
            self, documents: Sequence[Document], **kwargs: Any
    ) -> Generator[Document, None, None]:

        """Compress page content of raw documents asynchronously."""
        _callbacks = kwargs.get("callbacks", None)
        outputs = await asyncio.gather(
            *[
                self.llm_chain.apredict_and_parse(
                    **self.get_input(documents),
                    callbacks=_callbacks
                )
                for doc in documents
            ]
        )
        for i, doc in enumerate(documents):
            if not outputs[i]:
                continue
            yield Document(page_content=outputs[i],
                           metadata=copy.deepcopy(doc.metadata))

    async def atransform_documents(
            self, documents: Sequence[Document], **kwargs: Any
    ) -> Sequence[Document]:
        """Asynchronously transform a list of documents.

        Args:
            documents: A sequence of Documents to be transformed.

        Returns:
            A list of transformed Documents.
        """
        # FIXME: a tester. Lazy ?
        return await asyncio.get_running_loop().run_in_executor(
            None, partial(self.transform_documents, **kwargs), documents
        )

    @classmethod
    def from_llm(
            cls,
            llm: BaseLanguageModel,
            prompt: Optional[PromptTemplate] = None,
            get_input: Optional[Callable[[Document], dict]] = None,
            nb_of_questions: int = 3,
            llm_chain_kwargs: Optional[dict] = None,
    ) -> 'GenerateQuestions':
        """Initialize from LLM."""
        _prompt = prompt if prompt is not None else _get_default_chain_prompt()
        _get_input = get_input if get_input is not None else _default_get_input
        llm_chain = LLMChain(llm=llm, prompt=_prompt, **(llm_chain_kwargs or {}))
        return cls(llm_chain=llm_chain,
                   get_input=_get_input,
                   nb_of_questions=nb_of_questions)
