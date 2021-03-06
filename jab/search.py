from inspect import isfunction
from typing import Type, Optional, get_type_hints, Callable, Any, Union

from typing_extensions import Protocol, _get_protocol_attrs  # type: ignore


class ReturnedUnionType(Exception):
    pass


def isimplementation(cls_: Optional[Type[Any]], proto: Type[Any]) -> bool:
    """
    `isimplementation` checks to see if a provided class definition implement a provided Protocol definition.

    Parameters
    ----------
    cls_ : Any
        A concrete class defintiion
    proto : Any
        A protocol definition

    Returns
    -------
    bool
        Returns whether or not the provided class definition is a valid
        implementation of the provided Protocol.
    """
    if cls_ is None:
        return False

    proto_annotations = get_type_hints(proto)
    cls_annotations = get_type_hints(cls_)

    for attr in _get_protocol_attrs(proto):
        try:
            proto_concrete = getattr(proto, attr)
            cls_concrete = getattr(cls_, attr)
        except AttributeError:
            proto_concrete = proto_annotations.get(attr)
            cls_concrete = cls_annotations.get(attr)

        if cls_concrete is None:
            return False

        if isfunction(proto_concrete):
            if not func_satisfies(cls_concrete, proto_concrete):
                return False

            continue

        if cls_concrete != proto_concrete:
            return False

    return True


def func_satisfies(impl: Callable[..., Any], proto: Callable[..., Any]) -> bool:
    proto_signature = get_type_hints(proto)

    try:
        impl_signature = get_type_hints(impl)
    except AttributeError:
        return False

    if issubclass(proto_signature.get("return"), Protocol):  # type: ignore
        proto_return: Type[Any] = proto_signature["return"]
        cls_return: Optional[Type[Any]] = impl_signature.get("return")
        if isimplementation(cls_return, proto_return):
            impl_signature["return"] = proto_signature["return"]

    for param, proto_type in proto_signature.items():
        try:
            impl_type = impl_signature[param]
        except KeyError:
            return False

        try:
            # Handle the case in which the Implementation
            # implements a satisfactory method with Union
            # types
            if impl_type.__origin__ is Union:
                if proto_type not in impl_type.__args__:
                    return False

                if param == "return":
                    raise ReturnedUnionType(
                        f"Returned Union type found in {impl} implementation of {proto}. "
                        + f"Desired type {proto_type} is present in {impl_type} but jab cannot determine"
                        + f"if the desired type will be returned from defined input."
                    )

                continue
        except AttributeError:
            pass

        if proto_type != impl_type:
            return False

    return True
