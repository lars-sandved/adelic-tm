"""
Neary-Woods U18,2: 18-state 2-symbol strongly universal Turing machine.

From: "Four small universal Turing machines" (Neary & Woods, MCU 2007)
Table 15, pages 10-11.

This machine simulates bi-tag systems. It is STRONGLY universal:
it works from a blank tape background (symbol 'c') — no infinite
non-blank pattern required.

Symbols: c=0, b=1 (binary encoding)
States: u1..u18 (we use 1..18, with 0 unused)

The machine has 3 cycles:
  Cycle 1 (u1-u6): Index next production
  Cycle 2 (u7-u15): Print production  
  Cycle 3 (u15-u18): Restore tape

No explicit halt state — halting is detected by entering a repeating
configuration (the bi-tag system encodes halt as a cycle).
"""

from turing import TuringMachine, L, R

# Symbols: c=0, b=1
c, b = 0, 1


def neary_woods_u18_2() -> TuringMachine:
    """
    Construct the U18,2 universal Turing machine.
    
    Transition table from Table 15 of Neary & Woods (MCU 2007).
    Format: (state, symbol) -> (new_state, write_symbol, direction)
    
    States are numbered 1-18 (u1-u18).
    Symbols: 0=c (blank), 1=b
    """
    # Extracted directly from Table 15 in the paper:
    #
    #  U18,2  u1      u2      u3      u4      u5      u6      u7      u8      u9
    #  c      bRu2    cRu1    —       cLu5    cLu5    cLu4    bRu2    cLu8    bRu12
    #  b      bRu3    bRu1    bLu9    bLu6    cLu4    cLu4    bLu9    bLu7    bLu7
    #
    #  (u9 reading c = bLu10)
    #
    #  U18,2  u10     u11     u12     u13     u14     u15     u16     u17     u18
    #  c      cRu13   —       bLu7    cRu11   cLu15   cRu13   bLu9    cRu17   cRu15
    #  b      bRu15   bRu12   bRu11   bRu14   bRu13   —       cRu16   bRu15   cRu18
    #
    # (u18 reading b = cRu1)
    # Note: some cells have no entry (undefined = halt/no transition)
    
    table = {
        # Cycle 1: Index next production (u1-u6)
        (1, c): (2, b, R),    # u1,c -> bRu2
        (1, b): (3, b, R),    # u1,b -> bRu3
        (2, c): (1, c, R),    # u2,c -> cRu1
        (2, b): (1, b, R),    # u2,b -> bRu1
        # u3,c: undefined (triggers cycle 2 transition)
        (3, b): (9, b, L),    # u3,b -> bLu9  (detected bc = end of index scan right)
        (4, c): (5, c, L),    # u4,c -> cLu5
        (4, b): (6, b, L),    # u4,b -> bLu6
        (5, c): (5, c, L),    # u5,c -> cLu5 (keep scanning left past c's)
        (5, b): (4, c, L),    # u5,b -> cLu4
        (6, c): (4, c, L),    # u6,c -> cLu4
        (6, b): (4, c, L),    # u6,b -> cLu4  (found cb -> change to bb, re-enter cycle 1)
        # Wait - let me re-read. u6,c -> bRu2 according to the first sub-table
        # and u6,b -> cLu4. Let me re-check.
        # From Table 15 first half:
        # u6: c -> bRu2, b -> cLu4
        # Hmm that contradicts what I wrote. Let me re-extract carefully.
    }
    
    # Let me re-extract more carefully from the PDF text.
    # The table is split into two halves:
    #
    # FIRST HALF (Table 15, first row):
    #   States: u1  u2  u3  u4  u5  u6  u7  u8  u9
    #   c row:  bRu2  cRu1  cLu5  cLu5  cLu4  bRu2  cLu8  bRu12  bLu10
    #   b row:  bRu3  bRu1  bLu9  bLu6  cLu4  cLu4  bLu9  bLu7   bLu7
    #
    # SECOND HALF (Table 15, second row):
    #   States: u10  u11  u12  u13  u14  u15  u16  u17  u18
    #   c row:  cRu13  bLu7  cRu11  cLu15  cRu13  bLu9  cRu17  cRu15  —
    #   b row:  bRu15  bRu12  bRu11  bRu14  bRu13  cRu16  bRu15  cRu18  cRu1
    #
    # Wait, the PDF extraction is messy. Let me look at the raw text again:
    # "c bRu2 cRu1 cLu5 cLu5 cLu4 bRu2 cLu8 bRu12 bLu10"
    # "b bRu3 bRu1 bLu9 bLu6 cLu4 cLu4 bLu9 bLu7 bLu7"
    #
    # So for u3,c there IS an entry: cLu5. Let me fix.
    # And u6,c -> bRu2, u6,b -> cLu4
    # u9,c -> bLu10 (not bRu12)

    table = {
        # === FIRST HALF: u1-u9 ===
        # u1
        (1, c): (2, b, R),     # bRu2
        (1, b): (3, b, R),     # bRu3
        # u2
        (2, c): (1, c, R),     # cRu1
        (2, b): (1, b, R),     # bRu1
        # u3
        (3, c): (5, c, L),     # cLu5
        (3, b): (9, b, L),     # bLu9
        # u4
        (4, c): (5, c, L),     # cLu5
        (4, b): (6, b, L),     # bLu6
        # u5
        (5, c): (4, c, L),     # cLu4
        (5, b): (4, c, L),     # cLu4
        # u6
        (6, c): (2, b, R),     # bRu2
        (6, b): (4, c, L),     # cLu4
        # u7
        (7, c): (8, c, L),     # cLu8
        (7, b): (9, b, L),     # bLu9
        # u8
        (8, c): (12, b, R),    # bRu12
        (8, b): (7, b, L),     # bLu7
        # u9
        (9, c): (10, b, L),    # bLu10
        (9, b): (7, b, L),     # bLu7
        
        # === SECOND HALF: u10-u18 ===
        # u10
        (10, c): (13, c, R),   # cRu13
        (10, b): (15, b, R),   # bRu15
        # u11
        # (11, c): undefined
        (11, b): (12, b, R),   # bRu12
        # u12
        (12, c): (11, c, R),   # cRu11
        (12, b): (11, b, R),   # bRu11
        # u13
        (13, c): (15, c, L),   # cLu15
        (13, b): (14, b, R),   # bRu14
        # u14
        (14, c): (13, c, R),   # cRu13
        (14, b): (13, b, R),   # bRu13
        # u15
        # (15, c): undefined
        (15, b): (16, c, R),   # cRu16
        # u16
        (16, c): (17, c, R),   # cRu17
        (16, b): (15, b, R),   # bRu15
        # u17
        (17, c): (15, c, R),   # cRu15
        (17, b): (18, c, R),   # cRu18
        # u18
        # (18, c): undefined
        (18, b): (1, c, R),    # cRu1 — returns to Cycle 1!
    }
    
    # Note: undefined transitions mean the machine halts (or rather,
    # enters a state where no further computation is possible).
    # U18,2 has NO explicit halt — it simulates bi-tag systems that
    # encode halting as a repeating configuration.
    
    return TuringMachine(table, initial_state=1, halt_states=set())


def encode_bi_tag_dataword(symbols: list[tuple[str, int]], q: int) -> list[int]:
    """
    Encode a bi-tag system dataword for U18,2.
    
    From Table 2:
      <ai> = (bc)^{4i-1}  where a_i is the i-th A-symbol (1-indexed)
      <ej> = (bc)^{4jq}   where e_j is the j-th E-symbol
    
    Symbols between pairs are separated by bb (= 11).
    End marker: (bc)^2 = bcbc = 1010
    
    Args:
        symbols: list of ('a', index) or ('e', index) tuples (1-indexed)
        q: number of A-symbols in the bi-tag system
    
    Returns:
        list of tape cells (0s and 1s)
    """
    tape = []
    bc = [1, 0]  # b=1, c=0
    bb = [1, 1]  # separator
    
    for idx, (sym_type, sym_idx) in enumerate(symbols):
        if sym_type == 'a':
            # <ai> = (bc)^{4i-1}
            count = 4 * sym_idx - 1
        else:  # 'e'
            # <ej> = (bc)^{4j*q}
            count = 4 * sym_idx * q
        
        for _ in range(count):
            tape.extend(bc)
        
        # Add separator bb between symbols (not after last)
        if idx < len(symbols) - 1:
            tape.extend(bb)
    
    # End marker D = (bc)^2
    tape.extend(bb)  # separator before D
    tape.extend(bc * 2)  # D = (bc)^2
    
    return tape


# === Simple test bi-tag systems ===

def simple_bi_tag_system_1():
    """
    A trivial bi-tag system for testing the encoding.
    
    A = {a1}, E = {e1}
    P(a1) = a1  (identity on A-symbols)
    P(e1, a1) = a1 e1  (basic production)
    
    This just bounces between configurations, good for verifying
    the TM correctly indexes and prints productions.
    """
    return {
        'A': ['a1'],
        'E': ['e1'],
        'productions': {
            'a1': 'a1',
            ('e1', 'a1'): ('a1', 'e1'),
        }
    }
