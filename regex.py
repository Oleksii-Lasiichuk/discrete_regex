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

    def check_next(self, next_char: str) -> State | Exception:
        for state in self.next_states:
            if state.check_self(next_char):
                return state
        raise Exception("rejected string")


class StartState(State):
    def __init__(self):
        super().__init__()

    def check_self(self, char):
        return False


class TerminationState(State):
    def __init__(self):
        super().__init__()
        self.is_terminal = True
    
    def check_self(self, char):
        return False
        
    def check_next(self, next_char: str) -> State | Exception:
        raise Exception("rejected string")


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


class CharacterClassState(State):
    """
    State for character classes like [a-z], [0-9], etc.
    """
    def __init__(self, pattern: str) -> None:
        super().__init__()
        self.pattern = pattern
        self.negated = pattern.startswith('^')
        content = pattern[1:] if self.negated else pattern
        self.ranges = []
        i = 0
        while i < len(content):
            if i + 2 < len(content) and content[i+1] == '-':
                start, end = content[i], content[i+2]
                self.ranges.append((start, end))
                i += 3
            else:
                self.ranges.append((content[i], content[i]))
                i += 1

    def check_self(self, char: str) -> bool:
        in_range = False
        for start, end in self.ranges:
            if ord(start) <= ord(char) <= ord(end):
                in_range = True
                break
        return not in_range if self.negated else in_range


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

    def check_self(self, char):
        return self.checking_state.check_self(char)


class RegexFSM:
    def __init__(self, regex_expr: str) -> None:
        if not regex_expr:
            raise ValueError("Empty regex pattern")
        self.regex = regex_expr
        if regex_expr.startswith('*') or regex_expr.startswith('+'):
            raise ValueError(f"Invalid regex pattern: {regex_expr}")
        self._parse_pattern()
    
    def _parse_pattern(self):
        """Parse the regex pattern into a structured format"""
        self.parsed_pattern = []
        i = 0
        
        while i < len(self.regex):
            if self.regex[i] == '[':
                j = i + 1
                while j < len(self.regex) and self.regex[j] != ']':
                    j += 1
                
                if j >= len(self.regex):
                    raise ValueError("Unmatched bracket in regex pattern")
                class_content = self.regex[i+1:j]
                
                if j + 1 < len(self.regex) and self.regex[j+1] == '*':
                    self.parsed_pattern.append(('star_class', class_content))
                    i = j + 2
                elif j + 1 < len(self.regex) and self.regex[j+1] == '+':
                    self.parsed_pattern.append(('plus_class', class_content))
                    i = j + 2
                else:
                    self.parsed_pattern.append(('class', class_content))
                    i = j + 1
            elif i + 1 < len(self.regex) and self.regex[i+1] == '*':
                if self.regex[i] == '.':
                    self.parsed_pattern.append(('star', '.'))
                else:
                    self.parsed_pattern.append(('star', self.regex[i]))
                i += 2
            elif i + 1 < len(self.regex) and self.regex[i+1] == '+':
                if self.regex[i] == '.':
                    self.parsed_pattern.append(('plus', '.'))
                else:
                    self.parsed_pattern.append(('plus', self.regex[i]))
                i += 2
            elif self.regex[i] == '*' or self.regex[i] == '+':
                i += 1
            else:
                self.parsed_pattern.append(('char', self.regex[i]))
                i += 1
    
    def check_string(self, string: str) -> bool:
        """Check if the input string matches the regex pattern"""
        return self._match(0, 0, string)
    
    def _match(self, pattern_pos, string_pos, string):
        """
        Recursive backtracking algorithm to match the regex pattern against the string
        """
        if pattern_pos >= len(self.parsed_pattern):
            return string_pos >= len(string)

        token_type, token_value = self.parsed_pattern[pattern_pos]
        if token_type == 'char':
            if token_value == '.':
                if string_pos < len(string):
                    return self._match(pattern_pos + 1, string_pos + 1, string)
            else:
                if string_pos < len(string) and string[string_pos] == token_value:
                    return self._match(pattern_pos + 1, string_pos + 1, string)

        elif token_type == 'class':
            if string_pos < len(string) and self._match_character_class(token_value, string[string_pos]):
                return self._match(pattern_pos + 1, string_pos + 1, string)

        elif token_type == 'star':
            if self._match(pattern_pos + 1, string_pos, string):
                return True

            i = string_pos
            while i < len(string):
                matched = False
                if token_value == '.':
                    matched = True
                else:
                    matched = string[i] == token_value
                
                if not matched:
                    break

                if self._match(pattern_pos + 1, i + 1, string):
                    return True
                i += 1

        elif token_type == 'plus':

            if string_pos >= len(string):
                return False

            matched = False
            if token_value == '.':
                matched = True
            else:
                matched = string[string_pos] == token_value
            
            if not matched:
                return False
            i = string_pos + 1
            while i <= len(string):

                if self._match(pattern_pos + 1, i, string):
                    return True

                if i >= len(string):
                    break

                matched = False
                if token_value == '.':
                    matched = True
                else:
                    matched = string[i] == token_value
                if not matched:
                    break
                i += 1
        elif token_type == 'star_class':

            if self._match(pattern_pos + 1, string_pos, string):
                return True

            i = string_pos
            while i < len(string):
                if not self._match_character_class(token_value, string[i]):
                    break

                if self._match(pattern_pos + 1, i + 1, string):
                    return True
                i += 1

        elif token_type == 'plus_class':
            if string_pos >= len(string) or not self._match_character_class(token_value, string[string_pos]):
                return False

            i = string_pos + 1
            while i <= len(string):
                if self._match(pattern_pos + 1, i, string):
                    return True
                if i >= len(string) or not self._match_character_class(token_value, string[i]):
                    break
                
                i += 1
        
        return False
    
    def _match_character_class(self, class_pattern, char):
        """Check if a character matches a character class pattern"""
        negated = class_pattern.startswith('^')
        content = class_pattern[1:] if negated else class_pattern
        
        in_range = False
        i = 0
        while i < len(content):
            if i + 2 < len(content) and content[i+1] == '-':
                start, end = content[i], content[i+2]
                if ord(start) <= ord(char) <= ord(end):
                    in_range = True
                    break
                i += 3
            else:
                if char == content[i]:
                    in_range = True
                    break
                i += 1
        
        return not in_range if negated else in_range

if __name__ == "__main__":
    regex_pattern = "a*4.+hi"

    regex_compiled = RegexFSM(regex_pattern)

    print(regex_compiled.check_string("aaaaaa4uhi"))  # True
    print(regex_compiled.check_string("4uhi"))  # True
    print(regex_compiled.check_string("meow"))  # False
