#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Nodes related to raising and making exceptions.

"""

from .ChildrenHavingMixins import (
    ChildrenHavingExceptionTypeExceptionValueMixin,
)
from .ExpressionBases import ExpressionBase, ExpressionNoSideEffectsMixin
from .ExpressionBasesGenerated import (
    ExpressionBuiltinMakeExceptionBase,
    ExpressionBuiltinMakeExceptionImportErrorBase,
)
from .NodeBases import StatementBase, StatementChildrenHavingBase
from .NodeMakingHelpers import makeStatementOnlyNodesFromExpressions


class StatementRaiseExceptionMixin(object):
    # Mixins are required to also specify slots
    __slots__ = ()

    @staticmethod
    def isStatementAborting():
        return True

    @staticmethod
    def isStatementRaiseException():
        return True

    @staticmethod
    def willRaiseAnyException():
        return True


class StatementRaiseException(
    StatementRaiseExceptionMixin, StatementChildrenHavingBase
):
    kind = "STATEMENT_RAISE_EXCEPTION"

    named_children = (
        "exception_type",
        "exception_value",
        "exception_trace",
        "exception_cause",
    )

    __slots__ = ("reraise_finally",)

    def __init__(
        self,
        exception_type,
        exception_value,
        exception_trace,
        exception_cause,
        source_ref,
    ):
        assert exception_type is not None

        if exception_type is None:
            assert exception_value is None

        if exception_value is None:
            assert exception_trace is None

        StatementChildrenHavingBase.__init__(
            self,
            values={
                "exception_type": exception_type,
                "exception_value": exception_value,
                "exception_trace": exception_trace,
                "exception_cause": exception_cause,
            },
            source_ref=source_ref,
        )

        self.reraise_finally = False

    def computeStatement(self, trace_collection):
        exception_type = trace_collection.onExpression(
            expression=self.subnode_exception_type, allow_none=True
        )

        # TODO: Limit by type.
        trace_collection.onExceptionRaiseExit(BaseException)

        if exception_type is not None and exception_type.willRaiseAnyException():
            from .NodeMakingHelpers import (
                makeStatementExpressionOnlyReplacementNode,
            )

            result = makeStatementExpressionOnlyReplacementNode(
                expression=exception_type, node=self
            )

            return (
                result,
                "new_raise",
                """\
Explicit raise already raises implicitly building exception type.""",
            )

        exception_value = trace_collection.onExpression(
            expression=self.subnode_exception_value, allow_none=True
        )

        if exception_value is not None and exception_value.willRaiseAnyException():
            result = makeStatementOnlyNodesFromExpressions(
                expressions=(exception_type, exception_value)
            )

            return (
                result,
                "new_raise",
                """\
Explicit raise already raises implicitly building exception value.""",
            )

        exception_trace = trace_collection.onExpression(
            expression=self.subnode_exception_trace, allow_none=True
        )

        if exception_trace is not None and exception_trace.willRaiseAnyException():
            result = makeStatementOnlyNodesFromExpressions(
                expressions=(exception_type, exception_value, exception_trace)
            )

            return (
                result,
                "new_raise",
                """\
Explicit raise already raises implicitly building exception traceback.""",
            )

        exception_cause = trace_collection.onExpression(
            expression=self.subnode_exception_cause, allow_none=True
        )

        if exception_cause is not None and exception_cause.willRaiseAnyException():
            result = makeStatementOnlyNodesFromExpressions(
                expressions=(exception_type, exception_cause)
            )

            return (
                result,
                "new_raise",
                """
Explicit raise already raises implicitly building exception cause.""",
            )

        return self, None, None

    @staticmethod
    def needsFrame():
        return True

    @staticmethod
    def getStatementNiceName():
        return "exception raise statement"


class StatementRaiseExceptionImplicit(StatementRaiseException):
    kind = "STATEMENT_RAISE_EXCEPTION_IMPLICIT"

    @staticmethod
    def getStatementNiceName():
        return "implicit exception raise statement"


class StatementReraiseException(StatementRaiseExceptionMixin, StatementBase):
    kind = "STATEMENT_RERAISE_EXCEPTION"

    def finalize(self):
        del self.parent

    def computeStatement(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    # TODO: Not actually true, leads to wrong frame attached if there is
    # no pending exception.
    @staticmethod
    def needsFrame():
        return False

    @staticmethod
    def getStatementNiceName():
        return "exception re-raise statement"


class ExpressionRaiseException(
    ChildrenHavingExceptionTypeExceptionValueMixin, ExpressionBase
):
    """This node type is only produced via optimization.

    CPython only knows exception raising as a statement, but often the raising
    of exceptions can be predicted to occur as part of an expression, which it
    replaces then.
    """

    kind = "EXPRESSION_RAISE_EXCEPTION"

    named_children = ("exception_type", "exception_value")

    def __init__(self, exception_type, exception_value, source_ref):
        ChildrenHavingExceptionTypeExceptionValueMixin.__init__(
            self,
            exception_type=exception_type,
            exception_value=exception_value,
        )

        ExpressionBase.__init__(self, source_ref)

    @staticmethod
    def willRaiseAnyException():
        return True

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def computeExpressionDrop(self, statement, trace_collection):
        result = self.asStatement()

        del self.parent

        return (
            result,
            "new_raise",
            """\
Propagated implicit raise expression to raise statement.""",
        )

    def asStatement(self):
        return StatementRaiseExceptionImplicit(
            exception_type=self.subnode_exception_type,
            exception_value=self.subnode_exception_value,
            exception_trace=None,
            exception_cause=None,
            source_ref=self.source_ref,
        )


class ExpressionBuiltinMakeException(ExpressionBuiltinMakeExceptionBase):
    kind = "EXPRESSION_BUILTIN_MAKE_EXCEPTION"

    named_children = ("args|tuple",)

    __slots__ = ("exception_name",)

    # There is nothing to compute for it as a value.
    auto_compute_handling = "final,no_raise"

    def __init__(self, exception_name, args, source_ref):
        ExpressionBuiltinMakeExceptionBase.__init__(self, args, source_ref=source_ref)

        self.exception_name = exception_name

    def getDetails(self):
        return {"exception_name": self.exception_name}

    def getExceptionName(self):
        return self.exception_name

    def computeExpression(self, trace_collection):
        return self, None, None

    def mayRaiseException(self, exception_type):
        for arg in self.subnode_args:
            if arg.mayRaiseException(exception_type):
                return True

        return False


class ExpressionBuiltinMakeExceptionImportError(
    ExpressionBuiltinMakeExceptionImportErrorBase
):
    """Python3 ImportError dedicated node with extra arguments."""

    kind = "EXPRESSION_BUILTIN_MAKE_EXCEPTION_IMPORT_ERROR"

    named_children = ("args|tuple", "name|optional", "path|optional")

    __slots__ = ("exception_name",)

    # There is nothing to compute for it as a value.
    auto_compute_handling = "final,no_raise"

    @staticmethod
    def getExceptionName():
        return "ImportError"

    def computeExpression(self, trace_collection):
        return self, None, None

    def mayRaiseException(self, exception_type):
        for arg in self.subnode_args:
            if arg.mayRaiseException(exception_type):
                return True

        return False


class ExpressionCaughtMixin(ExpressionNoSideEffectsMixin):
    """Common things for all caught exception references."""

    __slots__ = ()

    def finalize(self):
        del self.parent


class ExpressionCaughtExceptionTypeRef(ExpressionCaughtMixin, ExpressionBase):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_TYPE_REF"

    def __init__(self, source_ref):
        ExpressionBase.__init__(self, source_ref)

    def computeExpressionRaw(self, trace_collection):
        # TODO: Might be predictable based on the exception handler this is in.
        return self, None, None


class ExpressionCaughtExceptionValueRef(ExpressionCaughtMixin, ExpressionBase):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_VALUE_REF"

    def __init__(self, source_ref):
        ExpressionBase.__init__(self, source_ref)

    def computeExpressionRaw(self, trace_collection):
        # TODO: Might be predictable based on the exception handler this is in.
        return self, None, None


class ExpressionCaughtExceptionTracebackRef(ExpressionCaughtMixin, ExpressionBase):
    kind = "EXPRESSION_CAUGHT_EXCEPTION_TRACEBACK_REF"

    def __init__(self, source_ref):
        ExpressionBase.__init__(self, source_ref)

    def computeExpressionRaw(self, trace_collection):
        return self, None, None
