"""Disassembler of Python byte code into mnemonics."""

import sys
import types

from opcode import *
from opcode import __all__ as _opcodes_all

__all__ = ["dis", "disassemble", "distb", "findlinestarts", "findlabels"] + _opcodes_all
del _opcodes_all

_have_code = (types.MethodType, types.FunctionType, types.CodeType,
              types.ClassType, type)


def dis(x=None):
    """Disassemble classes, methods, functions, or code.

    With no argument, disassemble the last traceback.

    """
    result = []
    if x is None:
        distb()
        return
    if isinstance(x, types.InstanceType):
        x = x.__class__
    if hasattr(x, 'im_func'):
        x = x.im_func
    if hasattr(x, 'func_code'):
        x = x.func_code
    if hasattr(x, '__dict__'):
        items = x.__dict__.items()
        items.sort()
        for name, x1 in items:
            if isinstance(x1, _have_code):
                result.append("Disassembly of %s:" % name)
                try:
                    dis(x1)
                except TypeError, msg:
                    result.append("Sorry:", msg)
                result.append('\n')
    elif hasattr(x, 'co_code'):
        result.extend(disassemble(x))
    elif isinstance(x, str):
        result.extend(disassemble_string(x))
    else:
        raise TypeError, \
            "don't know how to disassemble %s objects" % \
            type(x).__name__
    return result


def distb(tb=None):
    """Disassemble a traceback (default: last traceback)."""
    if tb is None:
        try:
            tb = sys.last_traceback
        except AttributeError:
            raise RuntimeError, "no last traceback to disassemble"
        while tb.tb_next: tb = tb.tb_next
    return disassemble(tb.tb_frame.f_code, tb.tb_lasti)


def disassemble(co, lasti=-1):
    """Disassemble a code object."""
    result = []
    code = co.co_code
    labels = findlabels(code)
    linestarts = dict(findlinestarts(co))
    n = len(code)
    i = 0
    extended_arg = 0
    free = None
    while i < n:
        c = code[i]
        op = ord(c)
        if i in linestarts:
            if i > 0:
                result.append()
            result.append("%3d" % linestarts[i], )
        else:
            result.append('   ', )

        if i == lasti:
            result.append('-->', )
        else:
            result.append('   ', )
        if i in labels:
            result.append('>>', )
        else:
            result.append('  ', )
        result.append(repr(i).rjust(4), )
        result.append(opname[op].ljust(20), )
        i = i + 1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i + 1]) * 256 + extended_arg
            extended_arg = 0
            i = i + 2
            try:
                if op == EXTENDED_ARG:
                    extended_arg = oparg * 65536L
                result.append(repr(oparg).rjust(5), )
                if op in hasconst:
                    result.append('(' + repr(co.co_consts[oparg]) + ')', )
                elif op in hasname:
                    result.append('(' + co.co_names[oparg] + ')', )
                elif op in hasjrel:
                    result.append('(to ' + repr(i + oparg) + ')', )
                elif op in haslocal:
                    result.append('(' + co.co_varnames[oparg] + ')', )
                elif op in hascompare:
                    result.append('(' + cmp_op[oparg] + ')', )
                elif op in hasfree:
                    if free is None:
                        free = co.co_cellvars + co.co_freevars
                    result.append('(' + free[oparg] + ')', )
            except KeyError:
                result.append(oparg)
        result.append()
    return result


def disassemble_string(code, lasti=-1, varnames=None, names=None,
                       constants=None):
    result = []
    labels = findlabels(code)
    n = len(code)
    i = 0
    while i < n:
        c = code[i]
        op = ord(c)
        if i == lasti:
            result.append('-->', )
        else:
            result.append('   ', )
        if i in labels:
            result.append('>>', )
        else:
            result.append('  ', )
        result.append(repr(i).rjust(4), )
        result.append(opname[op].ljust(15), )
        i = i + 1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i + 1]) * 256
            i = i + 2
            result.append(repr(oparg).rjust(5), )
            if op in hasconst:
                if constants:
                    result.append('(' + repr(constants[oparg]) + ')', )
                else:
                    result.append('(%d)' % oparg, )
            elif op in hasname:
                if names is not None:
                    result.append('(' + names[oparg] + ')', )
                else:
                    result.append('(%d)' % oparg, )
            elif op in hasjrel:
                result.append('(to ' + repr(i + oparg) + ')', )
            elif op in haslocal:
                if varnames:
                    result.append('(' + varnames[oparg] + ')', )
                else:
                    result.append('(%d)' % oparg, )
            elif op in hascompare:
                result.append('(' + cmp_op[oparg] + ')', )
        result.append('\n')
    return result


def findlabels(code):
    """Detect all offsets in a byte code which are jump targets.

    Return the list of offsets.

    """
    labels = []
    n = len(code)
    i = 0
    while i < n:
        c = code[i]
        op = ord(c)
        i = i + 1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i + 1]) * 256
            i = i + 2
            label = -1
            if op in hasjrel:
                label = i + oparg
            elif op in hasjabs:
                label = oparg
            if label >= 0:
                if label not in labels:
                    labels.append(label)
    return labels


def findlinestarts(code):
    """Find the offsets in a byte code which are start of lines in the source.

    Generate pairs (offset, lineno) as described in Python/compile.c.

    """
    byte_increments = [ord(c) for c in code.co_lnotab[0::2]]
    line_increments = [ord(c) for c in code.co_lnotab[1::2]]
    result = []
    lastlineno = None
    lineno = code.co_firstlineno
    addr = 0
    for byte_incr, line_incr in zip(byte_increments, line_increments):
        if byte_incr:
            if lineno != lastlineno:
                result.append((addr, lineno))
                lastlineno = lineno
            addr += byte_incr
        lineno += line_incr
    if lineno != lastlineno:
        result.append((addr, lineno))
    return result
