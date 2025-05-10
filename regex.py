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
        # Start state doesn't match any characters
        return False


class TerminationState(State):
    def __init__(self):
        super().__init__()
        self.is_terminal = True
    
    def check_self(self, char):
        # Termination doesn't accept any characters
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
        # Dot accepts any character
        return True


class AsciiState(State):
    """
    state for alphabet letters or numbers
    """
    def __init__(self, symbol: str) -> None:
        super().__init__()
        self.symbol = symbol

    def check_self(self, char: str) -> bool:
        # Check if the character matches this state's symbol
        return char == self.symbol


class CharacterClassState(State):
    """
    State for character classes like [a-z], [0-9], etc.
    """
    def __init__(self, pattern: str) -> None:
        super().__init__()
        self.pattern = pattern
        self.negated = pattern.startswith('^')
        
        # If negated, remove the ^ character
        content = pattern[1:] if self.negated else pattern
        
        # Parse the pattern to determine valid character ranges
        self.ranges = []
        i = 0
        while i < len(content):
            if i + 2 < len(content) and content[i+1] == '-':
                # This is a range, like 'a-z' or '0-9'
                start, end = content[i], content[i+2]
                self.ranges.append((start, end))
                i += 3
            else:
                # Single character
                self.ranges.append((content[i], content[i]))
                i += 1

    def check_self(self, char: str) -> bool:
        # Check if the character is within any of the defined ranges
        in_range = False
        for start, end in self.ranges:
            if ord(start) <= ord(char) <= ord(end):
                in_range = True
                break
        
        # If negated, return the opposite
        return not in_range if self.negated else in_range


class StarState(State):
    """
    State for * repetition (0 or more)
    """
    def __init__(self, checking_state: State):
        super().__init__()
        self.checking_state = checking_state

    def check_self(self, char):
        # Star can match if the checking state matches
        return self.checking_state.check_self(char)


class PlusState(State):
    """
    State for + repetition (1 or more)
    """
    def __init__(self, checking_state: State):
        super().__init__()
        self.checking_state = checking_state

    def check_self(self, char):
        # Plus needs to match at least once
        return self.checking_state.check_self(char)


class RegexFSM:
    def __init__(self, regex_expr: str) -> None:
        # Validate the regex pattern
        if not regex_expr:
            raise ValueError("Empty regex pattern")
            
        # Store the original pattern
        self.regex = regex_expr
        
        # Handle special cases like * and + at the beginning
        if regex_expr.startswith('*') or regex_expr.startswith('+'):
            raise ValueError(f"Invalid regex pattern: {regex_expr}")
        
        # Parse and compile the pattern
        self._parse_pattern()
    
    def _parse_pattern(self):
        """Parse the regex pattern into a structured format"""
        self.parsed_pattern = []
        i = 0
        
        while i < len(self.regex):
            if self.regex[i] == '[':
                # Handle character class
                j = i + 1
                while j < len(self.regex) and self.regex[j] != ']':
                    j += 1
                
                if j >= len(self.regex):
                    raise ValueError("Unmatched bracket in regex pattern")
                
                # Extract the character class content
                class_content = self.regex[i+1:j]
                
                # Check if followed by * or +
                if j + 1 < len(self.regex) and self.regex[j+1] == '*':
                    self.parsed_pattern.append(('star_class', class_content))
                    i = j + 2  # Skip the closing bracket and *
                elif j + 1 < len(self.regex) and self.regex[j+1] == '+':
                    self.parsed_pattern.append(('plus_class', class_content))
                    i = j + 2  # Skip the closing bracket and +
                else:
                    self.parsed_pattern.append(('class', class_content))
                    i = j + 1  # Skip the closing bracket
            elif i + 1 < len(self.regex) and self.regex[i+1] == '*':
                # Handle * operator
                if self.regex[i] == '.':
                    self.parsed_pattern.append(('star', '.'))
                else:
                    self.parsed_pattern.append(('star', self.regex[i]))
                i += 2
            elif i + 1 < len(self.regex) and self.regex[i+1] == '+':
                # Handle + operator
                if self.regex[i] == '.':
                    self.parsed_pattern.append(('plus', '.'))
                else:
                    self.parsed_pattern.append(('plus', self.regex[i]))
                i += 2
            elif self.regex[i] == '*' or self.regex[i] == '+':
                # Skip if we've already handled this as part of the previous character
                i += 1
            else:
                # Regular character
                self.parsed_pattern.append(('char', self.regex[i]))
                i += 1
    
    def check_string(self, string: str) -> bool:
        """Check if the input string matches the regex pattern"""
        # Use backtracking algorithm to match the string
        return self._match(0, 0, string)
    
    def _match(self, pattern_pos, string_pos, string):
        """
        Recursive backtracking algorithm to match the regex pattern against the string
        """
        # Base case: If we've reached the end of the pattern
        if pattern_pos >= len(self.parsed_pattern):
            return string_pos >= len(string)  # Match only if we've consumed the entire string
        
        token_type, token_value = self.parsed_pattern[pattern_pos]
        
        # Handle different token types
        if token_type == 'char':
            if token_value == '.':
                # Dot matches any single character
                if string_pos < len(string):
                    return self._match(pattern_pos + 1, string_pos + 1, string)
            else:
                # Regular character match
                if string_pos < len(string) and string[string_pos] == token_value:
                    return self._match(pattern_pos + 1, string_pos + 1, string)
        
        elif token_type == 'class':
            # Character class match
            if string_pos < len(string) and self._match_character_class(token_value, string[string_pos]):
                return self._match(pattern_pos + 1, string_pos + 1, string)
        
        elif token_type == 'star':
            # * operator: match 0 or more occurrences
            
            # First try matching 0 occurrences (skip the repeated element)
            if self._match(pattern_pos + 1, string_pos, string):
                return True
            
            # Try matching 1 or more occurrences
            i = string_pos
            while i < len(string):
                # Check if current character matches the token being repeated
                matched = False
                if token_value == '.':
                    matched = True  # Dot matches any character
                else:
                    matched = string[i] == token_value
                
                if not matched:
                    break
                
                # Try to match the rest of the pattern
                if self._match(pattern_pos + 1, i + 1, string):
                    return True
                
                i += 1
        
        elif token_type == 'plus':
            # + operator: match 1 or more occurrences
            
            # Must match at least one occurrence
            if string_pos >= len(string):
                return False
            
            # Check if the first character matches
            matched = False
            if token_value == '.':
                matched = True  # Dot matches any character
            else:
                matched = string[string_pos] == token_value
            
            if not matched:
                return False
            
            # Try matching additional occurrences
            i = string_pos + 1
            while i <= len(string):
                # Try to match the rest of the pattern from this position
                if self._match(pattern_pos + 1, i, string):
                    return True
                
                # If reached end of string or next character doesn't match, stop
                if i >= len(string):
                    break
                
                # Check if current character matches the token being repeated
                matched = False
                if token_value == '.':
                    matched = True  # Dot matches any character
                else:
                    matched = string[i] == token_value
                
                if not matched:
                    break
                
                i += 1
                
        elif token_type == 'star_class':
            # * operator with character class: match 0 or more occurrences
            
            # First try matching 0 occurrences (skip the repeated element)
            if self._match(pattern_pos + 1, string_pos, string):
                return True
            
            # Try matching 1 or more occurrences
            i = string_pos
            while i < len(string):
                # Check if current character matches the character class
                if not self._match_character_class(token_value, string[i]):
                    break
                
                # Try to match the rest of the pattern
                if self._match(pattern_pos + 1, i + 1, string):
                    return True
                
                i += 1
                
        elif token_type == 'plus_class':
            # + operator with character class: match 1 or more occurrences
            
            # Must match at least one occurrence
            if string_pos >= len(string) or not self._match_character_class(token_value, string[string_pos]):
                return False
            
            # Try matching additional occurrences
            i = string_pos + 1
            while i <= len(string):
                # Try to match the rest of the pattern from this position
                if self._match(pattern_pos + 1, i, string):
                    return True
                
                # If reached end of string or next character doesn't match, stop
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
                # This is a range, like 'a-z' or '0-9'
                start, end = content[i], content[i+2]
                if ord(start) <= ord(char) <= ord(end):
                    in_range = True
                    break
                i += 3
            else:
                # Single character
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
