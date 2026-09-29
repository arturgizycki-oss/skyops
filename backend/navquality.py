"""How sure the platform is about WHERE something is.

The detection confidence answers "how sure are we what this is". This
answers the other half: "how sure are we where it is". Both have to be
visible, because a finding is only actionable when both hold.

Position quality degrades for ordinary reasons - poor satellite
geometry in a valley, multipath between buildings - and for deliberate
ones. GNSS interference is a documented, routine fact in eastern
Poland. Either way the platform's duty is the same: report the
uncertainty, never invent precision it does not have.

The operational consequence matters more than the label. A finding with
an unreliable position must not be allowed to declare a road impassable,
because that sends a crew to the wrong place. Degraded position
downgrades a finding rather than colouring it.
"""

OK, DEGRADED, DENIED = "ok", "degraded", "denied"

# metres of expected error, for the operator to read
ACCURACY_M = {OK: 3, DEGRADED: 35, DENIED: None}

LABEL_PL = {
    OK: "pozycja pewna",
    DEGRADED: "pozycja przyblizona",
    DENIED: "pozycja niepewna",
}
LABEL_EN = {
    OK: "position good",
    DEGRADED: "position approximate",
    DENIED: "position unreliable",
}


class NavQuality:
    """Current position quality, and why.

    A real installation reads this from the receiver - satellite count,
    HDOP, RTK fix type. Here it is set explicitly and every response
    says `simulated: true`, so nobody can mistake the demo for a
    measurement.
    """

    def __init__(self) -> None:
        self.state = OK
        self.reason = ""
        self.simulated = False

    def set(self, state: str, reason: str = "") -> bool:
        if state not in (OK, DEGRADED, DENIED):
            return False
        self.state = state
        self.reason = reason
        self.simulated = state != OK
        return True

    @property
    def usable(self) -> bool:
        """Can a finding recorded now support a dispatch decision?"""
        return self.state == OK

    def picture(self) -> dict:
        return {
            "state": self.state,
            "reason": self.reason,
            "accuracy_m": ACCURACY_M[self.state],
            "usable": self.usable,
            "simulated": self.simulated,
            "label_pl": LABEL_PL[self.state],
            "label_en": LABEL_EN[self.state],
        }


nav = NavQuality()
