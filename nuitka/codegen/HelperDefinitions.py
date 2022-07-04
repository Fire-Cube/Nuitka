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
""" Shared definitions of what helpers are available.

These are functions to work with helper names, as well as sets of functions to
generate specialized code variants for.

Note: These are ordered, so we can define the order they are created in the
code generation of specialized helpers, as this set is used for input there
too.

"""

from nuitka.containers.OrderedSets import OrderedSet, buildOrderedSet

# spell-checker: ignore clong


def parseTypesFromHelper(helper_name):
    """Function to parse helper names."""

    if "_INPLACE" not in helper_name:
        target_code = helper_name.split("_")[3]
        left_code = helper_name.split("_")[4]
        right_code = helper_name.split("_")[5]
    else:
        target_code = None
        left_code = helper_name.split("_")[3]
        right_code = helper_name.split("_")[4]

    return target_code, left_code, right_code


def deriveInplaceFromBinaryOperations(operations_set):
    """Derive the in-place operations from the binary ones.

    These can largely be the same, or should be, and keeping them inline is easier when
    generating them. Obviously the templates might both need changes to optimize equally
    well for all variants.
    """

    if not operations_set:
        return None

    operation = next(iter(operations_set)).split("_")[2]

    return OrderedSet(
        helper_name.replace(operation + "_OBJECT", operation) + "_INPLACE"
        for helper_name in operations_set
        if parseTypesFromHelper(helper_name)[0] == "OBJECT"
        if "CLONG"
        not in parseTypesFromHelper(
            helper_name
        )  # TODO: In-place template must be enhanced for these.
    )


def _makeTypeOps(op_code, type_name, include_nbool):
    yield "BINARY_OPERATION_%s_OBJECT_%s_%s" % (op_code, type_name, type_name)
    yield "BINARY_OPERATION_%s_OBJECT_OBJECT_%s" % (op_code, type_name)
    yield "BINARY_OPERATION_%s_OBJECT_%s_OBJECT" % (op_code, type_name)

    if include_nbool:
        for helper in _makeTypeOpsNbool(op_code, type_name):
            yield helper


def _makeTypeOpsNbool(op_code, type_name):
    yield "BINARY_OPERATION_%s_NBOOL_%s_%s" % (op_code, type_name, type_name)
    yield "BINARY_OPERATION_%s_NBOOL_OBJECT_%s" % (op_code, type_name)
    yield "BINARY_OPERATION_%s_NBOOL_%s_OBJECT" % (op_code, type_name)


def _makeFriendOps(op_code, include_nbool, *type_names):
    for type_name1 in type_names:
        for type_name2 in type_names:
            if type_name1 == type_name2:
                continue

            yield "BINARY_OPERATION_%s_OBJECT_%s_%s" % (op_code, type_name1, type_name2)
            yield "BINARY_OPERATION_%s_OBJECT_%s_%s" % (op_code, type_name2, type_name1)

            if include_nbool:
                yield "BINARY_OPERATION_%s_NBOOL_%s_%s" % (
                    op_code,
                    type_name1,
                    type_name2,
                )
                yield "BINARY_OPERATION_%s_NBOOL_%s_%s" % (
                    op_code,
                    type_name2,
                    type_name1,
                )


def _makeDefaultOps(op_code, include_nbool):
    yield "BINARY_OPERATION_%s_OBJECT_OBJECT_OBJECT" % op_code
    if include_nbool:
        yield "BINARY_OPERATION_%s_NBOOL_OBJECT_OBJECT" % op_code


def _makeNonContainerMathOps(op_code):
    for type_name in "TUPLE", "LIST", "DICT", "SET", "FROZENSET":
        if "BIT" in op_code and type_name == "SET":
            continue
        if "SUB" in op_code and type_name == "SET":
            continue

        for value in _makeTypeOps(op_code, type_name, include_nbool=True):
            yield value


specialized_add_helpers_set = buildOrderedSet(
    _makeTypeOps("ADD", "INT", include_nbool=True),
    _makeTypeOps("ADD", "LONG", include_nbool=True),
    _makeTypeOps("ADD", "FLOAT", include_nbool=True),
    _makeTypeOps("ADD", "STR", include_nbool=False),
    _makeTypeOps("ADD", "UNICODE", include_nbool=False),
    _makeTypeOps("ADD", "BYTES", include_nbool=False),
    _makeTypeOps("ADD", "TUPLE", include_nbool=False),
    _makeTypeOps("ADD", "LIST", include_nbool=True),
    # These are friends naturally, they all add with another
    _makeFriendOps("ADD", True, "INT", "LONG", "FLOAT"),
    # TODO: Make CLONG ready to join above group.
    # makeFriendOps("ADD", True, "INT", "CLONG"),
    # These are friends too.
    _makeFriendOps("ADD", True, "STR", "UNICODE"),
    # Default implementation.
    _makeDefaultOps("ADD", include_nbool=True),
)

nonspecialized_add_helpers_set = buildOrderedSet(
    _makeTypeOpsNbool("ADD", "STR"),  # Not really likely to be used.
    _makeTypeOpsNbool("ADD", "UNICODE"),  # Not really likely to be used.
    _makeTypeOpsNbool("ADD", "BYTES"),  # Not really likely to be used.
    _makeTypeOpsNbool("ADD", "TUPLE"),  # Not really likely to be used.
)

specialized_sub_helpers_set = buildOrderedSet(
    _makeTypeOps("SUB", "INT", include_nbool=True),
    _makeTypeOps("SUB", "LONG", include_nbool=True),
    _makeTypeOps("SUB", "FLOAT", include_nbool=True),
    # These are friends naturally, they all sub with another
    _makeFriendOps("SUB", True, "INT", "LONG", "FLOAT"),
    _makeDefaultOps("SUB", include_nbool=True),
)

# These made no sense to specialize for, nothing to gain.
nonspecialized_sub_helpers_set = buildOrderedSet(
    _makeTypeOps("SUB", "STR", include_nbool=True),
    _makeTypeOps("SUB", "UNICODE", include_nbool=True),
    _makeTypeOps("SUB", "BYTES", include_nbool=True),
    _makeNonContainerMathOps("SUB"),
)

specialized_mult_helpers_set = buildOrderedSet(
    _makeTypeOps("MULT", "INT", include_nbool=True),
    _makeTypeOps("MULT", "LONG", include_nbool=True),
    _makeTypeOps("MULT", "FLOAT", include_nbool=True),
    (
        "BINARY_OPERATION_MULT_OBJECT_CLONG_CLONG",
        "BINARY_OPERATION_MULT_OBJECT_INT_CLONG",
        "BINARY_OPERATION_MULT_OBJECT_CLONG_INT",
        #        "BINARY_OPERATION_MULT_OBJECT_LONG_CLONG",
        #        "BINARY_OPERATION_MULT_OBJECT_CLONG_LONG",
        "BINARY_OPERATION_MULT_OBJECT_OBJECT_STR",
        "BINARY_OPERATION_MULT_OBJECT_STR_OBJECT",
        "BINARY_OPERATION_MULT_OBJECT_INT_STR",
        "BINARY_OPERATION_MULT_OBJECT_STR_INT",
        "BINARY_OPERATION_MULT_OBJECT_LONG_STR",
        "BINARY_OPERATION_MULT_OBJECT_STR_LONG",
        "BINARY_OPERATION_MULT_OBJECT_OBJECT_UNICODE",
        "BINARY_OPERATION_MULT_OBJECT_UNICODE_OBJECT",
        "BINARY_OPERATION_MULT_OBJECT_INT_UNICODE",
        "BINARY_OPERATION_MULT_OBJECT_UNICODE_INT",
        "BINARY_OPERATION_MULT_OBJECT_LONG_UNICODE",
        "BINARY_OPERATION_MULT_OBJECT_UNICODE_LONG",
        "BINARY_OPERATION_MULT_OBJECT_OBJECT_TUPLE",
        "BINARY_OPERATION_MULT_OBJECT_TUPLE_OBJECT",
        "BINARY_OPERATION_MULT_OBJECT_INT_TUPLE",
        "BINARY_OPERATION_MULT_OBJECT_TUPLE_INT",
        "BINARY_OPERATION_MULT_OBJECT_LONG_TUPLE",
        "BINARY_OPERATION_MULT_OBJECT_TUPLE_LONG",
        "BINARY_OPERATION_MULT_OBJECT_OBJECT_LIST",
        "BINARY_OPERATION_MULT_OBJECT_LIST_OBJECT",
        "BINARY_OPERATION_MULT_OBJECT_INT_LIST",
        "BINARY_OPERATION_MULT_OBJECT_LIST_INT",
        "BINARY_OPERATION_MULT_OBJECT_LONG_LIST",
        "BINARY_OPERATION_MULT_OBJECT_LIST_LONG",
        "BINARY_OPERATION_MULT_OBJECT_OBJECT_BYTES",
        "BINARY_OPERATION_MULT_OBJECT_BYTES_OBJECT",
        "BINARY_OPERATION_MULT_OBJECT_LONG_BYTES",
        "BINARY_OPERATION_MULT_OBJECT_BYTES_LONG",
    ),
    # These are friends naturally, they all mul with another
    _makeFriendOps("MULT", True, "INT", "LONG", "FLOAT"),
    _makeDefaultOps("MULT", include_nbool=True),
)

nonspecialized_mult_helpers_set = None

specialized_truediv_helpers_set = buildOrderedSet(
    _makeTypeOps("TRUEDIV", "INT", include_nbool=True),
    _makeTypeOps("TRUEDIV", "LONG", include_nbool=True),
    _makeTypeOps("TRUEDIV", "FLOAT", include_nbool=True),
    # These are friends naturally, they div mul with another
    _makeFriendOps("TRUEDIV", True, "INT", "LONG", "FLOAT"),
    _makeDefaultOps("TRUEDIV", include_nbool=True),
)

nonspecialized_truediv_helpers_set = buildOrderedSet(
    _makeTypeOps("TRUEDIV", "UNICODE", include_nbool=True),
    _makeTypeOps("TRUEDIV", "STR", include_nbool=True),
    _makeTypeOps("TRUEDIV", "BYTES", include_nbool=True),
    _makeNonContainerMathOps("TRUEDIV"),
)

specialized_olddiv_helpers_set = OrderedSet(
    helper.replace("TRUEDIV", "OLDDIV") for helper in specialized_truediv_helpers_set
)

nonspecialized_olddiv_helpers_set = OrderedSet(
    helper.replace("TRUEDIV", "OLDDIV") for helper in nonspecialized_truediv_helpers_set
)

specialized_floordiv_helpers_set = OrderedSet(
    helper.replace("TRUEDIV", "FLOORDIV") for helper in specialized_truediv_helpers_set
)

nonspecialized_floordiv_helpers_set = OrderedSet(
    helper.replace("TRUEDIV", "FLOORDIV")
    for helper in nonspecialized_truediv_helpers_set
)

specialized_mod_helpers_set = buildOrderedSet(
    _makeTypeOps("MOD", "INT", include_nbool=True),
    _makeTypeOps("MOD", "LONG", include_nbool=True),
    _makeTypeOps("MOD", "FLOAT", include_nbool=True),
    # These are friends naturally, they mod with another
    _makeFriendOps("MOD", True, "INT", "LONG", "FLOAT"),
    (
        # String interpolation with STR:
        "BINARY_OPERATION_MOD_OBJECT_STR_INT",
        "BINARY_OPERATION_MOD_OBJECT_STR_LONG",
        "BINARY_OPERATION_MOD_OBJECT_STR_FLOAT",
        "BINARY_OPERATION_MOD_OBJECT_STR_STR",
        "BINARY_OPERATION_MOD_OBJECT_STR_UNICODE",
        "BINARY_OPERATION_MOD_OBJECT_STR_TUPLE",
        "BINARY_OPERATION_MOD_OBJECT_STR_LIST",
        "BINARY_OPERATION_MOD_OBJECT_STR_DICT",
        "BINARY_OPERATION_MOD_OBJECT_STR_OBJECT",
        # String formatting with UNICODE:
        "BINARY_OPERATION_MOD_OBJECT_UNICODE_INT",
        "BINARY_OPERATION_MOD_OBJECT_UNICODE_LONG",
        "BINARY_OPERATION_MOD_OBJECT_UNICODE_FLOAT",
        "BINARY_OPERATION_MOD_OBJECT_UNICODE_STR",
        "BINARY_OPERATION_MOD_OBJECT_UNICODE_BYTES",
        "BINARY_OPERATION_MOD_OBJECT_UNICODE_UNICODE",
        "BINARY_OPERATION_MOD_OBJECT_UNICODE_TUPLE",
        "BINARY_OPERATION_MOD_OBJECT_UNICODE_LIST",
        "BINARY_OPERATION_MOD_OBJECT_UNICODE_DICT",
        "BINARY_OPERATION_MOD_OBJECT_UNICODE_OBJECT",
        # String formatting with BYTES:
        "BINARY_OPERATION_MOD_OBJECT_BYTES_BYTES",
        "BINARY_OPERATION_MOD_OBJECT_BYTES_LONG",
        "BINARY_OPERATION_MOD_OBJECT_BYTES_FLOAT",
        "BINARY_OPERATION_MOD_OBJECT_BYTES_UNICODE",
        "BINARY_OPERATION_MOD_OBJECT_BYTES_TUPLE",
        "BINARY_OPERATION_MOD_OBJECT_BYTES_LIST",
        "BINARY_OPERATION_MOD_OBJECT_BYTES_DICT",
        "BINARY_OPERATION_MOD_OBJECT_BYTES_OBJECT",
        # String formatting with OBJECT:
        "BINARY_OPERATION_MOD_OBJECT_OBJECT_STR",
        "BINARY_OPERATION_MOD_OBJECT_OBJECT_BYTES",
        "BINARY_OPERATION_MOD_OBJECT_OBJECT_UNICODE",
        "BINARY_OPERATION_MOD_OBJECT_OBJECT_TUPLE",
        "BINARY_OPERATION_MOD_OBJECT_OBJECT_LIST",
        "BINARY_OPERATION_MOD_OBJECT_OBJECT_DICT",
        # Default implementation.
        "BINARY_OPERATION_MOD_OBJECT_OBJECT_OBJECT",
    ),
    _makeDefaultOps("MOD", include_nbool=True),
)

nonspecialized_mod_helpers_set = buildOrderedSet(
    (
        "BINARY_OPERATION_MOD_OBJECT_TUPLE_OBJECT",
        "BINARY_OPERATION_MOD_OBJECT_LIST_OBJECT",
        # String formatting with STR:
        "BINARY_OPERATION_MOD_NBOOL_STR_INT",
        "BINARY_OPERATION_MOD_NBOOL_STR_LONG",
        "BINARY_OPERATION_MOD_NBOOL_STR_FLOAT",
        "BINARY_OPERATION_MOD_NBOOL_STR_STR",
        "BINARY_OPERATION_MOD_NBOOL_STR_UNICODE",
        "BINARY_OPERATION_MOD_NBOOL_STR_TUPLE",
        "BINARY_OPERATION_MOD_NBOOL_STR_LIST",
        "BINARY_OPERATION_MOD_NBOOL_STR_DICT",
        "BINARY_OPERATION_MOD_NBOOL_STR_OBJECT",
        # String formatting with UNICODE:
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_INT",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_LONG",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_FLOAT",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_STR",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_BYTES",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_UNICODE",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_TUPLE",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_LIST",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_DICT",
        "BINARY_OPERATION_MOD_NBOOL_UNICODE_OBJECT",
    )
)

specialized_imod_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_mod_helpers_set
)

nonspecialized_imod_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_mod_helpers_set
)


specialized_bitor_helpers_set = buildOrderedSet(
    _makeTypeOps("BITOR", "LONG", include_nbool=True),
    _makeTypeOps("BITOR", "INT", include_nbool=True),
    _makeFriendOps("BITOR", True, "INT", "LONG"),
    (
        # Set containers can do this
        "BINARY_OPERATION_BITOR_OBJECT_SET_SET",
        "BINARY_OPERATION_BITOR_OBJECT_OBJECT_SET",
        "BINARY_OPERATION_BITOR_OBJECT_SET_OBJECT",
    ),
    _makeDefaultOps("BITOR", include_nbool=True),
)
nonspecialized_bitor_helpers_set = buildOrderedSet(
    _makeTypeOps("BITOR", "FLOAT", include_nbool=True),
    _makeNonContainerMathOps("BITOR"),
    _makeTypeOps("BITOR", "UNICODE", include_nbool=True),
    _makeTypeOps("BITOR", "STR", include_nbool=True),
    _makeTypeOps("BITOR", "BYTES", include_nbool=True),
)

specialized_bitand_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_BITAND_") for helper in specialized_bitor_helpers_set
)
nonspecialized_bitand_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_BITAND_") for helper in nonspecialized_bitor_helpers_set
)
specialized_bitxor_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_BITXOR_") for helper in specialized_bitor_helpers_set
)
nonspecialized_bitxor_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_BITXOR_") for helper in nonspecialized_bitor_helpers_set
)
specialized_lshift_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_LSHIFT_")
    for helper in specialized_bitor_helpers_set
    if "_SET" not in helper
    if "_TUPLE" not in helper
)
nonspecialized_lshift_helpers_set = buildOrderedSet(
    _makeTypeOps("BITOR", "FLOAT", include_nbool=True),
    _makeNonContainerMathOps("BITOR"),
)
nonspecialized_lshift_helpers_set = OrderedSet(
    helper.replace("_BITOR_", "_LSHIFT_") for helper in nonspecialized_bitor_helpers_set
)
specialized_rshift_helpers_set = OrderedSet(
    helper.replace("_LSHIFT_", "_RSHIFT_") for helper in specialized_lshift_helpers_set
)
nonspecialized_rshift_helpers_set = OrderedSet(
    helper.replace("_LSHIFT_", "_RSHIFT_")
    for helper in nonspecialized_lshift_helpers_set
)


specialized_pow_helpers_set = buildOrderedSet(
    # TODO: Disable nbool, makes no sense
    _makeTypeOps("POW", "FLOAT", include_nbool=True),
    _makeTypeOps("POW", "LONG", include_nbool=True),
    _makeTypeOps("POW", "INT", include_nbool=True),
    _makeFriendOps("POW", True, "INT", "LONG"),
    _makeDefaultOps("POW", include_nbool=True),
    (
        # Float is used by other types for ** operations.
        # TODO: Enable these later.
        #        "BINARY_OPERATION_POW_OBJECT_LONG_FLOAT",
        #        "BINARY_OPERATION_POW_NBOOL_LONG_FLOAT",
    ),
)
nonspecialized_pow_helpers_set = buildOrderedSet(
    _makeTypeOps("POW", "STR", include_nbool=True),
    _makeTypeOps("POW", "UNICODE", include_nbool=True),
    _makeTypeOps("POW", "BYTES", include_nbool=True),
    _makeNonContainerMathOps("POW"),
)


specialized_divmod_helpers_set = buildOrderedSet(
    _makeTypeOps("DIVMOD", "INT", include_nbool=False),
    _makeTypeOps("DIVMOD", "LONG", include_nbool=False),
    _makeTypeOps("DIVMOD", "FLOAT", include_nbool=False),
    # These are friends naturally, they mod with another
    # makeFriendOps("DIVMOD", False, "INT", "LONG", "FLOAT"),
    _makeDefaultOps("DIVMOD", include_nbool=False),
)
nonspecialized_divmod_helpers_set = buildOrderedSet(
    _makeTypeOpsNbool("DIVMOD", "INT"),
    _makeTypeOpsNbool("DIVMOD", "LONG"),
    _makeTypeOpsNbool("DIVMOD", "FLOAT"),
    _makeTypeOps("DIVMOD", "UNICODE", include_nbool=True),
    _makeTypeOps("DIVMOD", "STR", include_nbool=True),
    _makeTypeOps("DIVMOD", "BYTES", include_nbool=True),
    _makeNonContainerMathOps("DIVMOD"),
)

assert (
    "BINARY_OPERATION_DIVMOD_OBJECT_TUPLE_OBJECT" in nonspecialized_divmod_helpers_set
)

specialized_matmult_helpers_set = buildOrderedSet(
    _makeTypeOps("MATMULT", "LONG", include_nbool=False),
    _makeTypeOps("MATMULT", "FLOAT", include_nbool=False),
    _makeDefaultOps("MATMULT", include_nbool=False),
)

nonspecialized_matmult_helpers_set = buildOrderedSet(
    _makeTypeOpsNbool("MATMULT", "LONG"),
    _makeTypeOpsNbool("MATMULT", "FLOAT"),
    _makeTypeOps("MATMULT", "TUPLE", include_nbool=True),
    _makeTypeOps("MATMULT", "LIST", include_nbool=True),
    _makeTypeOps("MATMULT", "DICT", include_nbool=True),
    _makeTypeOps("MATMULT", "BYTES", include_nbool=True),
    _makeTypeOps("MATMULT", "UNICODE", include_nbool=True),
)

specialized_iadd_helpers_set = buildOrderedSet(
    deriveInplaceFromBinaryOperations(specialized_add_helpers_set),
    ("BINARY_OPERATION_ADD_LIST_TUPLE_INPLACE",),
)
nonspecialized_iadd_helpers_set = buildOrderedSet(
    deriveInplaceFromBinaryOperations(nonspecialized_add_helpers_set),
    (
        "BINARY_OPERATION_ADD_LIST_STR_INPLACE",
        "BINARY_OPERATION_ADD_LIST_BYTES_INPLACE",
        "BINARY_OPERATION_ADD_LIST_BYTEARRAY_INPLACE",
        "BINARY_OPERATION_ADD_LIST_UNICODE_INPLACE",
        "BINARY_OPERATION_ADD_LIST_SET_INPLACE",  # semi useful only
        "BINARY_OPERATION_ADD_LIST_FROZENSET_INPLACE",
        "BINARY_OPERATION_ADD_LIST_DICT_INPLACE",
    ),
)

specialized_isub_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_sub_helpers_set
)
nonspecialized_isub_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_sub_helpers_set
)

specialized_imult_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_mult_helpers_set
)

nonspecialized_imult_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_mult_helpers_set
)

specialized_ibitor_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_bitor_helpers_set
)

nonspecialized_ibitor_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_bitor_helpers_set
)

specialized_ibitand_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_bitand_helpers_set
)

nonspecialized_ibitand_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_bitand_helpers_set
)

specialized_ibitxor_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_bitxor_helpers_set
)

nonspecialized_ibitxor_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_bitxor_helpers_set
)

specialized_ilshift_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_lshift_helpers_set
)

nonspecialized_ilshift_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_lshift_helpers_set
)

specialized_irshift_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_rshift_helpers_set
)

nonspecialized_irshift_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_rshift_helpers_set
)

specialized_ifloordiv_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_floordiv_helpers_set
)

nonspecialized_ifloordiv_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_floordiv_helpers_set
)

specialized_itruediv_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_truediv_helpers_set
)

nonspecialized_itruediv_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_truediv_helpers_set
)

specialized_iolddiv_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_olddiv_helpers_set
)

nonspecialized_iolddiv_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_olddiv_helpers_set
)

specialized_ipow_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_pow_helpers_set
)

nonspecialized_ipow_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_pow_helpers_set
)

specialized_imatmult_helpers_set = deriveInplaceFromBinaryOperations(
    specialized_matmult_helpers_set
)

nonspecialized_imatmult_helpers_set = deriveInplaceFromBinaryOperations(
    nonspecialized_matmult_helpers_set
)


def getSpecializedOperations(operator):
    return globals()["specialized_%s_helpers_set" % operator.lower()]


def getNonSpecializedOperations(operator):
    return globals()["nonspecialized_%s_helpers_set" % operator.lower()]


def getCodeNameForOperation(operator):
    return operator[1:].upper() if operator[0] == "I" else operator.upper()
