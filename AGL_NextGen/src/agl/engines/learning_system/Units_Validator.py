# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any, Optional

try:
    from pint import UnitRegistry # type: ignore
except Exception:
    UnitRegistry = None  # type: ignore


class UnitsValidator:
    """Simple dimensional-consistency checker using pint.

    Methods:
    - check_equation_units(equation_str, var_units) -> {ok: bool, errors: []}
      equation_str: something like 'F = m*a'
      var_units: dict mapping variable name to unit string, e.g. {'F': 'N', 'm':'kg', 'a':'m/s**2'}
    """

    def __init__(self):
        if UnitRegistry is None:
            raise RuntimeError("pint is not installed in the environment")
        self.ureg = UnitRegistry()

    def check_equation_units(self, equation_str: str, var_units: Dict[str, str]) -> Dict[str, Any]:
        """Check that both sides of equation have same dimensionality given var_units.

        var_units maps variable name -> unit expression understood by pint.
        Returns dict with ok (bool) and errors (list).
        """
        errors = []
        if UnitRegistry is None:
            return {"ok": False, "errors": ["pint_not_available"]}

        # prepare a local namespace with variables as quantified units
        ns = {}
        for k, u in (var_units or {}).items():
            try:
                ns[k] = 1 * self.ureg.parse_expression(u)
            except Exception as e:
                errors.append(f"unit_parse_error:{k}:{u}:{e}")

        # split equality
        if "=" in equation_str:
            left, right = equation_str.split("=", 1)
        else:
            left, right = equation_str, "0"

        try:
            # evaluate expressions using pint quantities
            lval = eval(left, {}, ns)
            rval = eval(right, {}, ns)
            # compare dimensionality
            if hasattr(lval, 'units') and hasattr(rval, 'units'):
                if lval.units == rval.units:
                    return {"ok": True, "errors": []}
                else:
                    return {"ok": False, "errors": [f"mismatched_units: {lval.units} != {rval.units}"]}
            else:
                return {"ok": False, "errors": ["no_unit_information"]}
        except Exception as e:
            errors.append(f"eval_error:{e}")
            return {"ok": False, "errors": errors}
