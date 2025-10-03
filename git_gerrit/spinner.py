# Copyright (c) 2025 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


import sys


class BaseSpinner:
    def __init__(self, message="", success="", error="failed"):
        self.message = message
        self.success = success
        self.error = error
        self.start()

    def start(self):
        pass

    def spin(self):
        pass

    def stop(self, message, success=True):
        pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.stop(self.error, success=False)
        else:
            self.stop(self.success, success=True)


class DummySpinner(BaseSpinner):
    """A spinner without animation for non-TTY output."""

    def __init__(self, message=""):
        super().__init__(message)

    def start(self):
        print(self.message)

    def spin(self):
        pass

    def stop(self, message, success=True):
        print(message)


class SimpleSpinner(BaseSpinner):
    """A simple animation spinner."""

    def __init__(self, message="Loading...", update_rate=10):
        if update_rate < 1:
            raise ValueError(f"Invalid update_rate {update_rate}")
        self.message = message
        self.spinner_chars = ['|', '/', '-', '\\']
        self.success_char = " "
        self.error_char_ = "x"
        self.spinner_index = 0
        self.update_rate = update_rate
        self.spin_count = 0
        super().__init__(message)

    def start(self):
        self._write_frame()

    def spin(self):
        """Advance the spinner animation."""
        self.spin_count += 1
        if self.spin_count % self.update_rate == 0:
            self.spinner_index += 1
            if self.spinner_index == len(self.spinner_chars):
                self.spinner_index = 0
            self._write_frame()

    def stop(self, message, success=True):
        """Stop the spinner, clears the line, and prints a final message."""
        clear_line = ' ' * (len(self.message) + 2)  # Clear the spinner line
        sys.stdout.write(f'\r{clear_line}\r')
        if success:
            frame = self.success_char
        else:
            frame = self.error_char
        print(f"\r{frame} {self.message} {message} ")
        sys.stdout.flush()

    def _write_frame(self):
        """Write the current animation frame to stdout."""
        frame = self.spinner_chars[self.spinner_index]
        sys.stdout.write(f"\r{frame} {self.message} ")
        sys.stdout.flush()


class FancySpinner(SimpleSpinner):
    """Fancy animation spinner."""

    def __init__(self, message="Loading...", update_rate=10):
        super().__init__(message, update_rate)
        self.success_char = "✔"
        self.error_char = "✘"

    def start(self):
        self.spinner_chars = ['⣷', '⣯', '⣟', '⡿', '⢿', '⣻', '⣽', '⣾']
        self._write_frame()


def Spinner(message="Loading...", update_rate=10):
    """
    Returns the appropriate spinner instance.

    Args:
        message (str): The message to display next to the spinner.
        update_rate (int): The number of spin() calls per animation frame.
    """
    if not sys.stdout.isatty():
        return DummySpinner(message)
    if "utf-8" in sys.stdout.encoding.lower():
        return FancySpinner(message, update_rate)
    return SimpleSpinner(message, update_rate)
