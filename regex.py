from __future__ import annotations
from abc import ABC, abstractmethod


class State(ABC):
    def __init__(self) -> None:
        self.next_states = []
        self.is_terminal = False

    @abstractmethod
    def check_self(self, char: str) -> bool:
        """
        function checks whether occured character is handled by current state
        """
        pass

    def check_next(self, next_char: str) -> State | None:
        for state in self.next_states:
            if state.check_self(next_char):
                return state
        return None


class StartState(State):
    def __init__(self):
        super().__init__()

    def check_self(self, char):
        return True


class TerminationState(State):
    def __init__(self):
        super().__init__()
        self.is_terminal = True
    
    def check_self(self, char):
        return False


class DotState(State):
    """
    state for . character (any character accepted)
    """
    def __init__(self):
        super().__init__()

    def check_self(self, char: str):
        return True


class AsciiState(State):
    """
    state for alphabet letters or numbers
    """
    def __init__(self, symbol: str) -> None:
        super().__init__()
        self.symbol = symbol

    def check_self(self, char: str) -> bool:
        return char == self.symbol


class StarState(State):
    """
    State for * repetition (0 or more)
    """
    def __init__(self, checking_state: State):
        super().__init__()
        self.checking_state = checking_state

    def check_self(self, char):
        return self.checking_state.check_self(char)


class PlusState(State):
    """
    State for + repetition (1 or more)
    """
    def __init__(self, checking_state: State):
        super().__init__()
        self.checking_state = checking_state
        self.counter = 0

    def check_self(self, char):
        result = self.checking_state.check_self(char)
        if result:
            self.counter += 1
        return result


class RegexFSM:
    def __init__(self, regex_expr: str) -> None:
        self.regex = regex_expr
    
    def _match_star(self, regex_index, string_index, string):
        """Handle * repetition matching"""
        char_to_repeat = self.regex[regex_index - 1]

        while string_index < len(string) and (string[string_index] == char_to_repeat or char_to_repeat == '.'):
            string_index += 1

        original_string_index = string_index
        for i in range(original_string_index, -1, -1):
            if self._match_from(regex_index + 1, i, string):
                return True
                
        return False
            
    def _match_plus(self, regex_index, string_index, string):
        """Handle + repetition matching"""
        char_to_repeat = self.regex[regex_index - 1]

        if string_index >= len(string) or (string[string_index] != char_to_repeat and char_to_repeat != '.'):
            return False
            
        while string_index < len(string) and (string[string_index] == char_to_repeat or char_to_repeat == '.'):
            string_index += 1

        original_string_index = string_index
        for i in range(original_string_index, -1, -1):
            if self._match_from(regex_index + 1, i, string):
                return True
                
        return False
            
    def _match_from(self, regex_index, string_index, string):
        """Recursively match the string from the given indices"""
        if regex_index >= len(self.regex):
            return string_index >= len(string)

        if regex_index + 1 < len(self.regex) and self.regex[regex_index + 1] == '*':
            return self._match_star(regex_index + 1, string_index, string)
            
        if regex_index + 1 < len(self.regex) and self.regex[regex_index + 1] == '+':
            return self._match_plus(regex_index + 1, string_index, string)

        if string_index < len(string) and (self.regex[regex_index] == '.' or self.regex[regex_index] == string[string_index]):
            return self._match_from(regex_index + 1, string_index + 1, string)
            
        return False

    def check_string(self, string: str) -> bool:
        """
        Check if the string matches the regex pattern using recursive backtracking
        """
        return self._match_from(0, 0, string)


if __name__ == "__main__":
    # regex_pattern = "a*4.+hi"

    # regex_compiled = RegexFSM(regex_pattern)

    # print(regex_compiled.check_string("aaaaaa4uhi"))  # Should be True
    # print(regex_compiled.check_string("4uhi"))  # Should be True
    # print(regex_compiled.check_string("meow"))  # Should be False
    regex_pattern = "a4.+hi+"

    regex_compiled = RegexFSM(regex_pattern)

    print(regex_compiled.check_string("a4uhi"))  # Should be True
    print(regex_compiled.check_string("a4hihi"))  # Should be True
    print(regex_compiled.check_string("4uhi"))  # false
    print(regex_compiled.check_string("meow"))  # Should be False
