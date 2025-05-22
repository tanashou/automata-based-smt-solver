from io import StringIO

import pysmt.smtlib.commands as smtcmd
from pysmt.fnode import FNode
from pysmt.smtlib.parser import SmtLibParser
from pysmt.smtlib.script import SmtLibScript

from automata_based_smt_solver.sat_status import SatStatus


class SMTLIBReader:
    def __init__(self) -> None:
        self.parser = SmtLibParser()

    def from_smt_lib(
        self, source: str, *, is_file_path: bool = False
    ) -> tuple[SatStatus, FNode]:
        if is_file_path:
            smt_script = self.parser.get_script_fname(source)
        else:
            smt_script = self.parser.get_script(StringIO(source))
        # SAT 情報と式を返す
        return self._get_sat_status(
            smt_script
        ), smt_script.get_strict_formula().simplify()

    def _get_sat_status(self, script: SmtLibScript) -> SatStatus:
        for cmd in script.commands:
            if cmd.name == smtcmd.SET_INFO and cmd.args[0] == ":status":
                return SatStatus(cmd.args[1])
        return SatStatus.UNKNOWN
