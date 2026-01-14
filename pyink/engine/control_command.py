from enum import IntEnum

from .object import InkObject


class ControlCommand(InkObject):
    class CommandType(IntEnum):
        NotSet = -1
        EvalStart = 0
        EvalOutput = 1
        EvalEnd = 2
        Duplicate = 3
        PopEvaluatedValue = 4
        PopFunction = 5
        PopTunnel = 6
        BeginString = 7
        EndString = 8
        NoOp = 9
        ChoiceCount = 10
        Turns = 11
        TurnsSince = 12
        ReadCount = 13
        Random = 14
        SeedRandom = 15
        VisitIndex = 16
        SequenceShuffleIndex = 17
        StartThread = 18
        Done = 19
        End = 20
        ListFromInt = 21
        ListRange = 22
        ListRandom = 23
        BeginTag = 24
        EndTag = 25
        TOTAL_VALUES = 26

    def __init__(self, command_type: "ControlCommand.CommandType" = CommandType.NotSet):
        super().__init__()
        self._commandType = command_type

    @property
    def commandType(self):
        return self._commandType

    def Copy(self):
        return ControlCommand(self.commandType)

    @staticmethod
    def EvalStart():
        return ControlCommand(ControlCommand.CommandType.EvalStart)

    @staticmethod
    def EvalOutput():
        return ControlCommand(ControlCommand.CommandType.EvalOutput)

    @staticmethod
    def EvalEnd():
        return ControlCommand(ControlCommand.CommandType.EvalEnd)

    @staticmethod
    def Duplicate():
        return ControlCommand(ControlCommand.CommandType.Duplicate)

    @staticmethod
    def PopEvaluatedValue():
        return ControlCommand(ControlCommand.CommandType.PopEvaluatedValue)

    @staticmethod
    def PopFunction():
        return ControlCommand(ControlCommand.CommandType.PopFunction)

    @staticmethod
    def PopTunnel():
        return ControlCommand(ControlCommand.CommandType.PopTunnel)

    @staticmethod
    def BeginString():
        return ControlCommand(ControlCommand.CommandType.BeginString)

    @staticmethod
    def EndString():
        return ControlCommand(ControlCommand.CommandType.EndString)

    @staticmethod
    def NoOp():
        return ControlCommand(ControlCommand.CommandType.NoOp)

    @staticmethod
    def ChoiceCount():
        return ControlCommand(ControlCommand.CommandType.ChoiceCount)

    @staticmethod
    def Turns():
        return ControlCommand(ControlCommand.CommandType.Turns)

    @staticmethod
    def TurnsSince():
        return ControlCommand(ControlCommand.CommandType.TurnsSince)

    @staticmethod
    def ReadCount():
        return ControlCommand(ControlCommand.CommandType.ReadCount)

    @staticmethod
    def Random():
        return ControlCommand(ControlCommand.CommandType.Random)

    @staticmethod
    def SeedRandom():
        return ControlCommand(ControlCommand.CommandType.SeedRandom)

    @staticmethod
    def VisitIndex():
        return ControlCommand(ControlCommand.CommandType.VisitIndex)

    @staticmethod
    def SequenceShuffleIndex():
        return ControlCommand(ControlCommand.CommandType.SequenceShuffleIndex)

    @staticmethod
    def StartThread():
        return ControlCommand(ControlCommand.CommandType.StartThread)

    @staticmethod
    def Done():
        return ControlCommand(ControlCommand.CommandType.Done)

    @staticmethod
    def End():
        return ControlCommand(ControlCommand.CommandType.End)

    @staticmethod
    def ListFromInt():
        return ControlCommand(ControlCommand.CommandType.ListFromInt)

    @staticmethod
    def ListRange():
        return ControlCommand(ControlCommand.CommandType.ListRange)

    @staticmethod
    def ListRandom():
        return ControlCommand(ControlCommand.CommandType.ListRandom)

    @staticmethod
    def BeginTag():
        return ControlCommand(ControlCommand.CommandType.BeginTag)

    @staticmethod
    def EndTag():
        return ControlCommand(ControlCommand.CommandType.EndTag)

    def __str__(self):
        return "ControlCommand " + str(self.commandType)
