import pygame
import chess
import random
import time
import threading
import math

# Enhanced Pygame setup - BIGGER BOARD
WIDTH, HEIGHT = 800, 640
BOARD_SIZE = 640  # Increased from 480 to 640
SQUARE_SIZE = BOARD_SIZE // 8
SIDEBAR_WIDTH = WIDTH - BOARD_SIZE
WHITE = (255, 255, 255)
GRAY = (125, 135, 150)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 100, 200)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
DARK_RED = (139, 0, 0)

# INSANE difficulty settings - AI WILL DOMINATE
DIFFICULTY_SETTINGS = {
    'Easy': {'depth': 5, 'randomness': 0.05, 'think_time': 1.0, 'aggression': 2.0, 'tactical_bonus': 1.5},
    'Medium': {'depth': 6, 'randomness': 0.02, 'think_time': 2.0, 'aggression': 2.8, 'tactical_bonus': 2.0},
    'Hard': {'depth': 7, 'randomness': 0.0, 'think_time': 3.5, 'aggression': 3.5, 'tactical_bonus': 2.5},
    'Expert': {'depth': 8, 'randomness': 0.0, 'think_time': 5.0, 'aggression': 4.2, 'tactical_bonus': 3.0},
    'Goat': {'depth': 9, 'randomness': 0.0, 'think_time': 8.0, 'aggression': 5.0, 'tactical_bonus': 4.0}
}

# Global transposition table with deeper storage
transposition_table = {}
killer_moves = {}  # Killer move heuristic
history_table = {}  # History heuristic

def load_images():
    """Load chess piece images with enhanced visuals"""
    pieces = ["wp", "wn", "wb", "wr", "wq", "wk", "bp", "bn", "bb", "br", "bq", "bk"]
    images = {}
    
    try:
        for piece in pieces:
            img = pygame.image.load(f"images/{piece}.png")
            images[piece] = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
        print("✅ Chess piece images loaded successfully!")
    except (pygame.error, FileNotFoundError):
        print("⚠️ Chess piece images not found. Using enhanced text-based pieces.")
        
        colors = {'w': (255, 255, 255), 'b': (30, 30, 30)}
        piece_chars = {'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'}
        
        pygame.font.init()
        font = pygame.font.Font(None, int(SQUARE_SIZE * 0.6))
        
        for piece in pieces:
            color = colors[piece[0]]
            surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            
            # Enhanced piece background
            pygame.draw.circle(surface, (220, 220, 220), 
                             (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE//2 - 5)
            pygame.draw.circle(surface, BLACK, 
                             (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE//2 - 5, 3)
            
            char = piece_chars.get(piece[1], piece[1].upper())
            text_color = (255, 255, 255) if color == (30, 30, 30) else (0, 0, 0)
            text = font.render(char, True, text_color)
            text_rect = text.get_rect(center=(SQUARE_SIZE//2, SQUARE_SIZE//2))
            surface.blit(text, text_rect)
            images[piece] = surface
    
    return images

def draw_board(screen, selected_square=None, possible_moves=None, last_move=None, threats=None, danger_level=0):
    colors = [WHITE, GRAY]
    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, color, rect)
            
            # Enhanced threat visualization
            if threats:
                square = chess.square(col, 7 - row)
                if square in threats:
                    threat_intensity = min(255, 100 + danger_level * 30)
                    threat_color = (threat_intensity, max(0, 165 - danger_level * 20), 0)
                    pygame.draw.rect(screen, threat_color, rect, 4)
            
            if last_move:
                from_row = 7 - (last_move.from_square // 8)
                from_col = last_move.from_square % 8
                to_row = 7 - (last_move.to_square // 8)
                to_col = last_move.to_square % 8
                
                if (row == from_row and col == from_col) or (row == to_row and col == to_col):
                    pygame.draw.rect(screen, YELLOW, rect, 4)
            
            if selected_square is not None:
                sel_row = 7 - (selected_square // 8)
                sel_col = selected_square % 8
                if row == sel_row and col == sel_col:
                    pygame.draw.rect(screen, LIGHT_BLUE, rect, 5)
            
            if possible_moves:
                square = chess.square(col, 7 - row)
                if square in possible_moves:
                    pygame.draw.circle(screen, GREEN, rect.center, 12)

def draw_pieces(screen, board, images):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            row = 7 - (square // 8)
            col = square % 8
            piece_str = piece.symbol()
            color = 'w' if piece_str.isupper() else 'b'
            piece_name = piece_str.lower()
            img_key = color + piece_name
            if img_key in images:
                piece_rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                screen.blit(images[img_key], piece_rect)

def draw_sidebar(screen, difficulty, game_status, captured_pieces, eval_score, thinking_time, move_count, ai_strategy, ai_depth):
    sidebar_rect = pygame.Rect(BOARD_SIZE, 0, SIDEBAR_WIDTH, HEIGHT)
    pygame.draw.rect(screen, (240, 240, 240), sidebar_rect)
    
    try:
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)
        title_font = pygame.font.Font(None, 28)
    except:
        font = pygame.font.SysFont('Arial', 24)
        small_font = pygame.font.SysFont('Arial', 18)
        title_font = pygame.font.SysFont('Arial', 28)
    
    y_pos = 10
    
    # Title
    title = title_font.render("Chess AI", True, DARK_RED)
    screen.blit(title, (BOARD_SIZE + 5, y_pos))
    y_pos += 35
    
    diff_colors = {'Easy': GREEN, 'Medium': ORANGE, 'Hard': RED, 'Expert': PURPLE, 'Goat': DARK_RED}
    diff_color = diff_colors.get(difficulty, BLACK)
    diff_text = font.render(f"Level: {difficulty}", True, diff_color)
    screen.blit(diff_text, (BOARD_SIZE + 5, y_pos))
    y_pos += 30
    
    if ai_strategy:
        strategy_lines = ai_strategy.split('\n')
        for line in strategy_lines[:2]:
            strategy_text = small_font.render(line, True, (150, 0, 0))
            screen.blit(strategy_text, (BOARD_SIZE + 5, y_pos))
            y_pos += 18
    y_pos += 10
    
    # Enhanced stats
    stats = [
        f"Moves: {move_count}",
        f"Depth: {ai_depth}",
        f"Eval: {eval_score:+.1f}",
        f"Think: {thinking_time:.1f}s"
    ]
    
    for stat in stats:
        if "Eval:" in stat:
            color = GREEN if eval_score > 0 else RED if eval_score < 0 else BLACK
        else:
            color = BLACK
        stat_text = small_font.render(stat, True, color)
        screen.blit(stat_text, (BOARD_SIZE + 5, y_pos))
        y_pos += 20
    
    y_pos += 10
    
    status_lines = game_status.split('\n')
    for line in status_lines:
        if line.strip():
            status_text = small_font.render(line, True, BLACK)
            screen.blit(status_text, (BOARD_SIZE + 5, y_pos))
            y_pos += 18
    
    y_pos += 15
    
    # Enhanced captured pieces display
    if captured_pieces.get('black'):
        cap_text = small_font.render("You captured:", True, BLACK)
        screen.blit(cap_text, (BOARD_SIZE + 5, y_pos))
        y_pos += 18
        piece_str = ''.join(captured_pieces['black'][:10])
        pieces_text = font.render(piece_str, True, BLACK)
        screen.blit(pieces_text, (BOARD_SIZE + 5, y_pos))
        y_pos += 30
    
    if captured_pieces.get('white'):
        cap_text = small_font.render("AI captured:", True, DARK_RED)
        screen.blit(cap_text, (BOARD_SIZE + 5, y_pos))
        y_pos += 18
        piece_str = ''.join(captured_pieces['white'][:10])
        pieces_text = font.render(piece_str, True, DARK_RED)
        screen.blit(pieces_text, (BOARD_SIZE + 5, y_pos))
        y_pos += 30
    
    # Enhanced instructions at bottom
    inst_y = HEIGHT - 180
    instructions = [
        "Controls:",
        "R - Restart",
        f"1 - Easy {'✓' if difficulty == 'Easy' else ''}", 
        f"2 - Medium {'✓' if difficulty == 'Medium' else ''}", 
        f"3 - Hard {'✓' if difficulty == 'Hard' else ''}",
        f"4 - Expert {'✓' if difficulty == 'Expert' else ''}",
        f"5 - Goat {'✓' if difficulty == 'Goat' else ''}",
        "U - Undo move",
        "Q - Quit"
    ]
    for i, inst in enumerate(instructions):
        if inst_y + i * 18 < HEIGHT - 10:
            color = BLACK
            if difficulty in inst and '✓' in inst:
                color = diff_colors.get(difficulty, BLACK)
            text = small_font.render(inst, True, color)
            screen.blit(text, (BOARD_SIZE + 5, inst_y + i * 18))

# INSANE piece values - AI prioritizes DESTRUCTION
PIECE_VALUES = {
    chess.PAWN: 120,      # Increased value
    chess.KNIGHT: 380,    # Knights are tactical destroyers
    chess.BISHOP: 390,    # Long-range assassins
    chess.ROOK: 600,      # Brutal power pieces
    chess.QUEEN: 1200,    # Ultimate weapon
    chess.KING: 0
}

# ULTRA AGGRESSIVE position tables
PAWN_TABLE = [
    [0,   0,   0,   0,   0,   0,   0,   0],
    [120, 120, 120, 120, 120, 120, 120, 120],  # 7th rank devastation
    [50,  50,  60,  80,  80,  60,  50,  50],   # 6th rank aggression
    [25,  25,  35,  60,  60,  35,  25,  25],   # 5th rank pressure
    [10,  10,  20,  45,  45,  20,  10,  10],   # 4th rank advance
    [5,   -5,  0,   20,  20,  0,   -5,  5],
    [5,   20,  20,  -15, -15, 20,  20,  5],
    [0,   0,   0,   0,   0,   0,   0,   0]
]

KNIGHT_TABLE = [
    [-100, -50, -30, -30, -30, -30, -50, -100],
    [-50,  -20,  20,  25,  25,  20, -20,  -50],
    [-30,   25,  40,  50,  50,  40,  25,  -30],  # Devastating central knights
    [-30,   20,  50,  60,  60,  50,  20,  -30],  # Ultra strong center
    [-30,   25,  50,  60,  60,  50,  25,  -30],
    [-30,   20,  40,  50,  50,  40,  20,  -30],
    [-50,  -20,  20,  25,  25,  20, -20,  -50],
    [-100, -50, -30, -30, -30, -30, -50, -100]
]

BISHOP_TABLE = [
    [-40, -20, -15, -15, -15, -15, -20, -40],
    [-20,  20,  25,  25,  25,  25,  20, -20],
    [-15,  25,  35,  40,  40,  35,  25, -15],  # Diagonal dominance
    [-15,  20,  40,  45,  45,  40,  20, -15],
    [-15,  25,  40,  45,  45,  40,  25, -15],
    [-15,  30,  35,  40,  40,  35,  30, -15],
    [-20,  25,  20,  20,  20,  20,  25, -20],
    [-40, -20, -15, -15, -15, -15, -20, -40]
]

ROOK_TABLE = [
    [20,  25,  25,  30,  30,  25,  25,  20],   # Aggressive back rank
    [25,  30,  30,  35,  35,  30,  30,  25],   # Devastating 7th rank
    [5,   10,  10,  10,  10,  10,  10,  5],
    [5,   10,  10,  10,  10,  10,  10,  5],
    [5,   10,  10,  10,  10,  10,  10,  5],
    [5,   10,  10,  10,  10,  10,  10,  5],
    [10,  20,  20,  20,  20,  20,  20,  10],
    [15,  20,  20,  25,  25,  20,  20,  15]
]

QUEEN_TABLE = [
    [-30, -10, -5,  0,   0,  -5, -10, -30],
    [-10,  0,   10, 10,  10,  10,  0,  -10],
    [-5,   10,  20, 20,  20,  20,  10, -5],
    [0,    10,  20, 25,  25,  20,  10,  0],    # Queen domination
    [0,    10,  20, 25,  25,  20,  10,  0],
    [-5,   20,  20, 20,  20,  20,  20, -5],
    [-10,  10,  20, 10,  10,  10,  10, -10],
    [-30, -10, -5,  0,   0,  -5, -10, -30]
]

KING_MIDDLE_GAME = [
    [-80, -70, -70, -80, -80, -70, -70, -80],
    [-60, -60, -60, -70, -70, -60, -60, -60],
    [-40, -40, -40, -60, -60, -40, -40, -40],
    [-30, -30, -30, -50, -50, -30, -30, -30],
    [-20, -20, -20, -40, -40, -20, -20, -20],
    [0,    0,   0,  -20, -20,  0,   0,   0],
    [40,  50,  30,   0,   0,  30,  50,  40],  # Strong castling incentive
    [60,  70,  50,  20,  20,  50,  70,  60]
]

def get_piece_square_value(piece, square, endgame=False):
    """Enhanced positional evaluation"""
    if not piece:
        return 0
    
    rank = chess.square_rank(square)
    file = chess.square_file(square)
    
    # Flip for black pieces
    if piece.color == chess.BLACK:
        rank = 7 - rank
    
    base_value = 0
    if piece.piece_type == chess.PAWN:
        base_value = PAWN_TABLE[rank][file]
    elif piece.piece_type == chess.KNIGHT:
        base_value = KNIGHT_TABLE[rank][file]
    elif piece.piece_type == chess.BISHOP:
        base_value = BISHOP_TABLE[rank][file]
    elif piece.piece_type == chess.ROOK:
        base_value = ROOK_TABLE[rank][file]
    elif piece.piece_type == chess.QUEEN:
        base_value = QUEEN_TABLE[rank][file]
    elif piece.piece_type == chess.KING:
        base_value = KING_MIDDLE_GAME[rank][file]
    
    return base_value

def is_endgame(board):
    """Enhanced endgame detection"""
    material_count = 0
    queens = 0
    minor_pieces = 0
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type != chess.KING:
            material_count += PIECE_VALUES.get(piece.piece_type, 0)
            if piece.piece_type == chess.QUEEN:
                queens += 1
            elif piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                minor_pieces += 1
    
    return material_count < 2500 or queens == 0 or minor_pieces <= 2

def count_attackers_defenders(board, square, attacking_color):
    """Advanced attacker/defender analysis"""
    attackers = []
    attacker_values = []
    
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece and piece.color == attacking_color:
            if square in board.attacks(sq):
                attackers.append(sq)
                attacker_values.append(PIECE_VALUES.get(piece.piece_type, 0))
    
    return len(attackers), attacker_values, attackers

def evaluate_king_safety(board, color):
    """BRUTAL king safety evaluation"""
    king_square = board.king(color)
    if not king_square:
        return 0
    
    safety_score = 0
    enemy_color = not color
    
    # Extended danger zone (5x5 area around king)
    danger_squares = []
    king_rank = chess.square_rank(king_square)
    king_file = chess.square_file(king_square)
    
    for rank_offset in range(-2, 3):
        for file_offset in range(-2, 3):
            new_rank = king_rank + rank_offset
            new_file = king_file + file_offset
            
            if 0 <= new_rank <= 7 and 0 <= new_file <= 7:
                danger_square = chess.square(new_file, new_rank)
                danger_squares.append(danger_square)
                
                # Distance-based penalty
                distance = max(abs(rank_offset), abs(file_offset))
                weight = 3.0 - distance * 0.5
                
                attacker_count, attacker_values, _ = count_attackers_defenders(board, danger_square, enemy_color)
                
                for attacker_value in attacker_values:
                    if attacker_value >= PIECE_VALUES[chess.QUEEN]:
                        safety_score -= 120 * weight  # Queen attacks are devastating
                    elif attacker_value >= PIECE_VALUES[chess.ROOK]:
                        safety_score -= 80 * weight
                    elif attacker_value >= PIECE_VALUES[chess.BISHOP]:
                        safety_score -= 50 * weight
                    elif attacker_value >= PIECE_VALUES[chess.KNIGHT]:
                        safety_score -= 60 * weight  # Knights are dangerous
                    elif attacker_value >= PIECE_VALUES[chess.PAWN]:
                        safety_score -= 30 * weight
    
    # Pawn shield evaluation (enhanced)
    pawn_shield_bonus = 0
    shield_ranks = [1, 2] if color == chess.WHITE else [6, 5]
    
    for rank in shield_ranks:
        for file_offset in [-1, 0, 1]:
            shield_file = king_file + file_offset
            if 0 <= shield_file <= 7:
                shield_square = chess.square(shield_file, rank)
                piece = board.piece_at(shield_square)
                if piece and piece.piece_type == chess.PAWN and piece.color == color:
                    pawn_shield_bonus += 35 if rank == shield_ranks[0] else 20
    
    # Open files near king penalty
    open_file_penalty = 0
    for file_offset in [-1, 0, 1]:
        check_file = king_file + file_offset
        if 0 <= check_file <= 7:
            has_pawn = False
            for rank in range(8):
                square = chess.square(check_file, rank)
                piece = board.piece_at(square)
                if piece and piece.piece_type == chess.PAWN:
                    has_pawn = True
                    break
            if not has_pawn:
                open_file_penalty -= 40
    
    return safety_score + pawn_shield_bonus + open_file_penalty

def evaluate_tactical_motifs(board, aggression_factor):
    """INSANE tactical pattern recognition"""
    score = 0
    
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    
    if not white_king or not black_king:
        return score
    
    # BRUTAL attack patterns
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == chess.BLACK:  # AI pieces
            attacks = list(board.attacks(square))
            
            for attack_square in attacks:
                target_piece = board.piece_at(attack_square)
                distance_to_white_king = chess.square_distance(attack_square, white_king)
                
                # Massive bonus for attacking near human king
                if distance_to_white_king <= 3:
                    base_bonus = 0
                    if piece.piece_type == chess.QUEEN:
                        base_bonus = 100
                    elif piece.piece_type == chess.ROOK:
                        base_bonus = 70
                    elif piece.piece_type == chess.BISHOP:
                        base_bonus = 45
                    elif piece.piece_type == chess.KNIGHT:
                        base_bonus = 55
                    elif piece.piece_type == chess.PAWN:
                        base_bonus = 25
                    
                    # Distance multiplier
                    distance_multiplier = 4.0 - distance_to_white_king
                    score += base_bonus * distance_multiplier * aggression_factor
                
                # Bonus for attacking valuable pieces
                if target_piece and target_piece.color == chess.WHITE:
                    target_value = PIECE_VALUES.get(target_piece.piece_type, 0)
                    attacker_value = PIECE_VALUES.get(piece.piece_type, 0)
                    
                    if target_value > attacker_value:
                        score += (target_value - attacker_value) * 0.8 * aggression_factor
                    elif target_value >= attacker_value:
                        score += target_value * 0.3 * aggression_factor
    
    # Penalty for human attacking AI king (but less severe - encourage aggression)
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == chess.WHITE:
            attacks = list(board.attacks(square))
            
            for attack_square in attacks:
                distance_to_black_king = chess.square_distance(attack_square, black_king)
                if distance_to_black_king <= 2:
                    score -= 25  # Reduced penalty to encourage AI risk-taking
    
    return score

def evaluate_pawn_structure(board, aggression_factor):
    """Advanced pawn structure evaluation"""
    score = 0
    
    white_pawns = []
    black_pawns = []
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type == chess.PAWN:
            if piece.color == chess.WHITE:
                white_pawns.append(square)
            else:
                black_pawns.append(square)
    
    # AI passed pawns get MASSIVE bonus
    for pawn_square in black_pawns:
        file = chess.square_file(pawn_square)
        rank = chess.square_rank(pawn_square)
        
        is_passed = True
        for enemy_pawn in white_pawns:
            enemy_file = chess.square_file(enemy_pawn)
            enemy_rank = chess.square_rank(enemy_pawn)
            
            if abs(enemy_file - file) <= 1 and enemy_rank < rank:
                is_passed = False
                break
        
        if is_passed:
            # Exponential bonus for advanced passed pawns
            advancement = rank + 1
            bonus = advancement * advancement * 20 * aggression_factor
            score += bonus
            
            # Extra bonus if supported
            support_squares = [pawn_square - 9, pawn_square - 7]
            for support_sq in support_squares:
                if 0 <= support_sq <= 63:
                    support_piece = board.piece_at(support_sq)
                    if (support_piece and support_piece.piece_type == chess.PAWN 
                        and support_piece.color == chess.BLACK):
                        score += 30 * aggression_factor
    
    # Human passed pawns get reduced penalty (AI takes risks)
    for pawn_square in white_pawns:
        file = chess.square_file(pawn_square)
        rank = chess.square_rank(pawn_square)
        
        is_passed = True
        for enemy_pawn in black_pawns:
            enemy_file = chess.square_file(enemy_pawn)
            enemy_rank = chess.square_rank(enemy_pawn)
            
            if abs(enemy_file - file) <= 1 and enemy_rank > rank:
                is_passed = False
                break
        
        if is_passed:
            advancement = 6 - rank
            penalty = advancement * 18  # Reduced penalty
            score -= penalty
    
    # Pawn chains and islands
    files_with_pawns = {'white': set(), 'black': set()}
    for pawn_square in white_pawns:
        files_with_pawns['white'].add(chess.square_file(pawn_square))
    for pawn_square in black_pawns:
        files_with_pawns['black'].add(chess.square_file(pawn_square))
    
    # Penalty for pawn islands (AI prefers connected pawns)
    def count_pawn_islands(files):
        if not files:
            return 0
        sorted_files = sorted(files)
        islands = 1
        for i in range(1, len(sorted_files)):
            if sorted_files[i] - sorted_files[i-1] > 1:
                islands += 1
        return islands
    
    white_islands = count_pawn_islands(files_with_pawns['white'])
    black_islands = count_pawn_islands(files_with_pawns['black'])
    
    score += (white_islands - black_islands) * 25
    
    return score

def evaluate_piece_activity(board, aggression_factor):
    """Reward hyperactive pieces"""
    score = 0
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            try:
                attacks = list(board.attacks(square))
                mobility = len(attacks)
                
                # Base mobility bonus
                if piece.color == chess.BLACK:  # AI pieces
                    if piece.piece_type == chess.QUEEN:
                        score += mobility * 8 * aggression_factor
                    elif piece.piece_type == chess.ROOK:
                        score += mobility * 6 * aggression_factor
                    elif piece.piece_type == chess.BISHOP:
                        score += mobility * 4 * aggression_factor
                    elif piece.piece_type == chess.KNIGHT:
                        score += mobility * 5 * aggression_factor  # Knights love mobility
                    elif piece.piece_type == chess.PAWN:
                        score += mobility * 3 * aggression_factor
                else:  # Human pieces (reduce their mobility value)
                    if piece.piece_type == chess.QUEEN:
                        score -= mobility * 4
                    elif piece.piece_type == chess.ROOK:
                        score -= mobility * 3
                    elif piece.piece_type == chess.BISHOP:
                        score -= mobility * 2
                    elif piece.piece_type == chess.KNIGHT:
                        score -= mobility * 3
                    elif piece.piece_type == chess.PAWN:
                        score -= mobility * 2
            except:
                pass
    
    return score

def evaluate_board(board, aggression_factor=1.0, tactical_bonus=1.0):
    """INSANELY AGGRESSIVE board evaluation - UNBEATABLE AI"""
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000
    
    if board.is_stalemate() or board.is_insufficient_material():
        return -5000  # AI hates draws
    
    score = 0
    endgame = is_endgame(board)
    
    # 1. BRUTAL Material evaluation
    white_material = 0
    black_material = 0
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            piece_value = PIECE_VALUES.get(piece.piece_type, 0)
            position_value = get_piece_square_value(piece, square, endgame)
            
            total_value = piece_value + position_value
            
            if piece.color == chess.WHITE:
                white_material += total_value
            else:
                black_material += total_value * 1.1  # AI pieces are more valuable
    
    score = black_material - white_material
    
    # 2. DEVASTATING King Safety evaluation
    white_king_safety = evaluate_king_safety(board, chess.WHITE)
    black_king_safety = evaluate_king_safety(board, chess.BLACK)
    
    # AI gets MASSIVE bonus for threatening human king
    score -= white_king_safety * 4.0 * aggression_factor
    score += black_king_safety * 1.5  # AI still protects own king
    
    # 3. BRUTAL tactical motifs
    tactical_score = evaluate_tactical_motifs(board, aggression_factor)
    score += tactical_score * tactical_bonus
    
    # 4. INSANE mobility advantage
    original_turn = board.turn
    
    try:
        board.turn = chess.WHITE
        white_moves = list(board.legal_moves)
        white_mobility = len(white_moves)
        
        board.turn = chess.BLACK  
        black_moves = list(board.legal_moves)
        black_mobility = len(black_moves)
        
        board.turn = original_turn
        
        # AI values its mobility WAY more
        mobility_diff = (black_mobility - white_mobility)
        score += mobility_diff * 8 * aggression_factor
        
        # Bonus for having many aggressive options
        black_captures = sum(1 for move in black_moves if board.is_capture(move))
        white_captures = sum(1 for move in white_moves if board.is_capture(move))
        
        score += (black_captures - white_captures) * 25 * aggression_factor
        
    except:
        board.turn = original_turn
    
    # 5. EXTREME center control
    center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
    extended_center = [chess.C3, chess.C4, chess.C5, chess.C6,
                      chess.D3, chess.D6, chess.E3, chess.E6,
                      chess.F3, chess.F4, chess.F5, chess.F6]
    
    for square in center_squares:
        piece = board.piece_at(square)
        if piece:
            if piece.color == chess.BLACK:  # AI
                score += 50 * aggression_factor
            else:
                score -= 35
        
        # BRUTAL control evaluation
        black_attackers, _, _ = count_attackers_defenders(board, square, chess.BLACK)
        white_attackers, _, _ = count_attackers_defenders(board, square, chess.WHITE)
        control_diff = black_attackers - white_attackers
        score += control_diff * 15 * aggression_factor
    
    # Extended center
    for square in extended_center:
        black_attackers, _, _ = count_attackers_defenders(board, square, chess.BLACK)
        white_attackers, _, _ = count_attackers_defenders(board, square, chess.WHITE)
        control_diff = black_attackers - white_attackers
        score += control_diff * 6 * aggression_factor
    
    # 6. AGGRESSIVE pawn structure
    pawn_score = evaluate_pawn_structure(board, aggression_factor)
    score += pawn_score
    
    # 7. HYPERACTIVE piece evaluation
    activity_score = evaluate_piece_activity(board, aggression_factor)
    score += activity_score
    
    # 8. DEVASTATING check bonus
    if board.is_check():
        if board.turn == chess.WHITE:  # Human is in check
            score += 200 * aggression_factor
        else:  # AI is in check
            score -= 100
    
    # 9. Advanced piece positioning bonuses
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == chess.BLACK:
            rank = chess.square_rank(square)
            
            # MASSIVE bonus for pieces advancing towards enemy
            if piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.QUEEN]:
                if rank <= 4:  # Advanced position for black
                    advancement_bonus = (5 - rank) * 30 * aggression_factor
                    score += advancement_bonus
            
            # Special queen aggression bonus
            if piece.piece_type == chess.QUEEN and rank <= 3:
                score += 100 * aggression_factor
    
    # 10. BRUTAL attacking combinations detection
    try:
        # Look for discovered attacks
        for move in board.legal_moves:
            if board.turn == chess.BLACK:  # AI turn
                board.push(move)
                if board.is_check():
                    score += 150 * aggression_factor  # Discovered check bonus
                
                # Look for forks, pins, skewers
                attacking_piece = board.piece_at(move.to_square)
                if attacking_piece:
                    attacks = list(board.attacks(move.to_square))
                    valuable_targets = 0
                    for attack_sq in attacks:
                        target = board.piece_at(attack_sq)
                        if target and target.color == chess.WHITE:
                            target_value = PIECE_VALUES.get(target.piece_type, 0)
                            if target_value >= PIECE_VALUES[chess.KNIGHT]:
                                valuable_targets += 1
                    
                    if valuable_targets >= 2:  # Potential fork
                        score += 80 * aggression_factor
                
                board.pop()
    except:
        pass
    
    # 11. Endgame specialization
    if endgame:
        # AI becomes even more aggressive in endgame
        score = int(score * 1.3)
        
        # King activity in endgame
        black_king = board.king(chess.BLACK)
        white_king = board.king(chess.WHITE)
        
        if black_king and white_king:
            # AI king should be active
            black_king_centralization = 0
            king_rank = chess.square_rank(black_king)
            king_file = chess.square_file(black_king)
            
            # Bonus for centralized king
            center_distance = abs(king_rank - 3.5) + abs(king_file - 3.5)
            black_king_centralization = int((7 - center_distance) * 20)
            score += black_king_centralization
            
            # Bonus for AI king approaching human king (for mating)
            king_distance = chess.square_distance(black_king, white_king)
            if king_distance <= 3:
                score += (4 - king_distance) * 50
    
    return int(score)

def advanced_move_ordering(board, moves, aggression_factor=1.0, depth=0):
    """INSANE move ordering for maximum alpha-beta efficiency"""
    if not moves:
        return []
    
    move_scores = []
    white_king = board.king(chess.WHITE)
    
    for move in moves:
        move_score = 0
        
        try:
            # 1. Captures (with advanced SEE - Static Exchange Evaluation)
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                
                if victim and attacker:
                    victim_value = PIECE_VALUES.get(victim.piece_type, 0)
                    attacker_value = PIECE_VALUES.get(attacker.piece_type, 0)
                    
                    # Advanced capture evaluation
                    capture_value = victim_value
                    
                    # Bonus for capturing with less valuable piece
                    if victim_value > attacker_value:
                        capture_value += (victim_value - attacker_value) * 0.5
                    
                    # MASSIVE bonus for capturing near enemy king
                    if white_king:
                        distance = chess.square_distance(move.to_square, white_king)
                        if distance <= 2:
                            capture_value += 300 * aggression_factor
                    
                    move_score += capture_value * 10
            
            # 2. Checks get HUGE priority
            board.push(move)
            gives_check = board.is_check()
            if gives_check:
                move_score += 2000 * aggression_factor
                
                # MASSIVE bonus for checkmate
                if board.is_checkmate():
                    move_score += 50000
            board.pop()
            
            # 3. Attacks on enemy king area
            if white_king:
                distance_to_king = chess.square_distance(move.to_square, white_king)
                if distance_to_king <= 3:
                    king_attack_bonus = (4 - distance_to_king) * 200 * aggression_factor
                    move_score += king_attack_bonus
            
            # 4. Piece advancement towards enemy
            piece = board.piece_at(move.from_square)
            if piece and piece.color == chess.BLACK:
                from_rank = chess.square_rank(move.from_square)
                to_rank = chess.square_rank(move.to_square)
                
                if to_rank < from_rank:  # Moving towards enemy
                    advancement = from_rank - to_rank
                    move_score += advancement * 20 * aggression_factor
            
            # 5. Central control
            center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
            if move.to_square in center_squares:
                move_score += 150 * aggression_factor
            
            # 6. Killer move heuristic
            global killer_moves
            move_key = f"{depth}_{move.uci()}"
            if move_key in killer_moves:
                move_score += killer_moves[move_key]
            
            # 7. History heuristic
            global history_table
            if move.uci() in history_table:
                move_score += history_table[move.uci()] * 0.1
            
            # 8. Promotion moves
            if move.promotion:
                if move.promotion == chess.QUEEN:
                    move_score += 1800 * aggression_factor
                elif move.promotion in [chess.ROOK, chess.KNIGHT]:
                    move_score += 1000 * aggression_factor
            
            # 9. Castling (defensive, but still important)
            if board.is_castling(move):
                move_score += 100
            
            move_scores.append((move, move_score))
            
        except Exception as e:
            # If there's an error, give the move a neutral score
            move_scores.append((move, 0))
    
    # Sort moves by score (highest first)
    move_scores.sort(key=lambda x: x[1], reverse=True)
    return [move for move, score in move_scores]

def quiescence_search(board, alpha, beta, depth, aggression_factor):
    """Quiescence search to avoid horizon effect"""
    if depth <= 0:
        return evaluate_board(board, aggression_factor)
    
    # Stand pat score
    stand_pat = evaluate_board(board, aggression_factor)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat
    
    # Only consider captures and checks in quiescence
    moves = []
    for move in board.legal_moves:
        if board.is_capture(move):
            moves.append(move)
        else:
            # Check if move gives check
            board.push(move)
            if board.is_check():
                moves.append(move)
            board.pop()
    
    if not moves:
        return stand_pat
    
    # Order captures by value
    moves = advanced_move_ordering(board, moves, aggression_factor, depth)
    
    for move in moves:
        try:
            board.push(move)
            score = -quiescence_search(board, -beta, -alpha, depth - 1, aggression_factor)
            board.pop()
            
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        except:
            try:
                board.pop()
            except:
                pass
    
    return alpha

def minimax_with_pruning(board, depth, alpha, beta, maximizing_player, start_time, max_time=30, aggression_factor=1.0, tactical_bonus=1.0):
    """ULTRA ADVANCED minimax with ALL optimizations"""
    
    # Time check
    if time.time() - start_time > max_time:
        return evaluate_board(board, aggression_factor, tactical_bonus)
    
    # Base case with quiescence search
    if depth == 0:
        return quiescence_search(board, alpha, beta, 3, aggression_factor)
    
    if board.is_game_over():
        return evaluate_board(board, aggression_factor, tactical_bonus)
    
    # Transposition table lookup
    board_hash = hash(board.fen())
    if board_hash in transposition_table:
        stored_depth, stored_score, stored_type = transposition_table[board_hash]
        if stored_depth >= depth:
            if stored_type == 'exact':
                return stored_score
            elif stored_type == 'lowerbound' and stored_score >= beta:
                return stored_score
            elif stored_type == 'upperbound' and stored_score <= alpha:
                return stored_score
    
    moves = list(board.legal_moves)
    if not moves:
        return evaluate_board(board, aggression_factor, tactical_bonus)
    
    # Advanced move ordering
    moves = advanced_move_ordering(board, moves, aggression_factor, depth)
    
    original_alpha = alpha
    best_move = None
    
    if maximizing_player:  # AI (Black) maximizing
        max_eval = float('-inf')
        
        for i, move in enumerate(moves):
            if time.time() - start_time > max_time:
                break
                
            try:
                board.push(move)
                
                # Late Move Reduction (LMR)
                reduction = 0
                if (depth >= 3 and i >= 4 and 
                    not board.is_capture(move) and not board.is_check()):
                    reduction = 1
                
                eval_score = -minimax_with_pruning(board, depth - 1 - reduction, -beta, -alpha, 
                                                 False, start_time, max_time, aggression_factor, tactical_bonus)
                
                # Re-search if LMR failed
                if reduction > 0 and eval_score > alpha:
                    eval_score = -minimax_with_pruning(board, depth - 1, -beta, -alpha, 
                                                     False, start_time, max_time, aggression_factor, tactical_bonus)
                
                board.pop()
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    # Update killer moves
                    global killer_moves
                    killer_key = f"{depth}_{move.uci()}"
                    killer_moves[killer_key] = killer_moves.get(killer_key, 0) + depth * depth
                    
                    # Update history table
                    global history_table
                    history_table[move.uci()] = history_table.get(move.uci(), 0) + depth * depth
                    
                    break  # Alpha-beta cutoff
                    
            except:
                try:
                    board.pop()
                except:
                    pass
                continue
        
        # Store in transposition table
        tt_type = 'exact'
        if max_eval <= original_alpha:
            tt_type = 'upperbound'
        elif max_eval >= beta:
            tt_type = 'lowerbound'
        
        transposition_table[board_hash] = (depth, max_eval, tt_type)
        return max_eval
    
    else:  # Human (White) minimizing
        min_eval = float('inf')
        
        for i, move in enumerate(moves):
            if time.time() - start_time > max_time:
                break
                
            try:
                board.push(move)
                
                # Late Move Reduction for human too
                reduction = 0
                if (depth >= 3 and i >= 4 and 
                    not board.is_capture(move) and not board.is_check()):
                    reduction = 1
                
                eval_score = -minimax_with_pruning(board, depth - 1 - reduction, -beta, -alpha, 
                                                 True, start_time, max_time, aggression_factor, tactical_bonus)
                
                if reduction > 0 and eval_score < beta:
                    eval_score = -minimax_with_pruning(board, depth - 1, -beta, -alpha, 
                                                     True, start_time, max_time, aggression_factor, tactical_bonus)
                
                board.pop()
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break  # Alpha-beta cutoff
                    
            except:
                try:
                    board.pop()
                except:
                    pass
                continue
        
        # Store in transposition table
        tt_type = 'exact'
        if min_eval <= original_alpha:
            tt_type = 'upperbound'
        elif min_eval >= beta:
            tt_type = 'lowerbound'
            
        transposition_table[board_hash] = (depth, min_eval, tt_type)
        return min_eval

def get_best_move(board, difficulty):
    """DESTROYER AI - Finds the most BRUTAL moves possible"""
    global transposition_table, killer_moves, history_table
    
    settings = DIFFICULTY_SETTINGS[difficulty]
    depth = settings['depth']
    randomness = settings['randomness']
    max_think_time = settings['think_time']
    aggression_factor = settings['aggression']
    tactical_bonus = settings['tactical_bonus']
    
    moves = list(board.legal_moves)
    if not moves:
        return None, "No legal moves"
    
    # Even "random" moves are aggressive
    if randomness > 0 and random.random() < randomness:
        aggressive_moves = []
        
        for move in moves:
            move_priority = 0
            
            if board.is_capture(move):
                move_priority += 100
            
            board.push(move)
            if board.is_check():
                move_priority += 200
            if board.is_checkmate():
                return move, "INSTANT CHECKMATE!"
            board.pop()
            
            # Attacks near king
            white_king = board.king(chess.WHITE)
            if white_king:
                distance = chess.square_distance(move.to_square, white_king)
                if distance <= 2:
                    move_priority += 150
            
            if move_priority > 50:
                aggressive_moves.append((move, move_priority))
        
        if aggressive_moves:
            aggressive_moves.sort(key=lambda x: x[1], reverse=True)
            return aggressive_moves[0][0], "Aggressive tactical move!"
        
        return random.choice(moves), "Fallback move"
    
    print(f"🔥💀 DESTROYER AI analyzing {len(moves)} moves at depth {depth} 💀🔥")
    print(f"⚔️ Aggression Factor: {aggression_factor}x | Tactical Bonus: {tactical_bonus}x")
    
    best_move = None
    best_score = float('-inf')
    start_time = time.time()
    
    # Advanced move ordering
    ordered_moves = advanced_move_ordering(board, moves, aggression_factor, depth)
    
    move_evaluations = []
    nodes_searched = 0
    
    # Iterative deepening for better time management
    for current_depth in range(1, depth + 1):
        if time.time() - start_time > max_think_time * 0.8:
            print(f"⏰ Time limit approaching, stopping at depth {current_depth-1}")
            break
        
        current_best = None
        current_best_score = float('-inf')
        
        for i, move in enumerate(ordered_moves):
            if time.time() - start_time > max_think_time:
                print(f"⏰ Time limit reached at depth {current_depth}, move {i+1}")
                break
                
            try:
                board.push(move)
                
                # Use full window search for first move, then null window for others
                if i == 0:
                    score = -minimax_with_pruning(board, current_depth - 1, float('-inf'), float('inf'), 
                                               False, start_time, max_think_time, aggression_factor, tactical_bonus)
                else:
                    # Null window search
                    score = -minimax_with_pruning(board, current_depth - 1, -current_best_score-1, -current_best_score, 
                                               False, start_time, max_think_time, aggression_factor, tactical_bonus)
                    
                    # Re-search if null window failed
                    if score > current_best_score:
                        score = -minimax_with_pruning(board, current_depth - 1, float('-inf'), float('inf'), 
                                                   False, start_time, max_think_time, aggression_factor, tactical_bonus)
                
                board.pop()
                nodes_searched += 1
                
                if i < 5 and current_depth == depth:  # Debug top moves at final depth
                    move_type = "CAPTURE" if board.is_capture(move) else "MOVE"
                    print(f"  💀 {move_type} {i+1}: {move.uci()} = {score}")
                
                if score > current_best_score:
                    current_best_score = score
                    current_best = move
                    
            except Exception as e:
                print(f"Error evaluating {move.uci()}: {e}")
                try:
                    board.pop()
                except:
                    pass
                continue
        
        if current_best:
            best_move = current_best
            best_score = current_best_score
            
            if current_depth >= 3:  # Start showing intermediate results
                print(f"🧠 Depth {current_depth}: {best_move.uci()} = {best_score}")
    
    if not best_move:
        # Emergency fallback - pick most aggressive move
        for move in moves:
            if board.is_capture(move):
                best_move = move
                break
        if not best_move:
            best_move = random.choice(moves)
        strategy = "EMERGENCY PROTOCOL!"
    else:
        # ULTRA AGGRESSIVE strategy descriptions
        if best_score > 2000:
            strategy = "💀 ANNIHILATION INCOMING! 💀\n🔥 TOTAL DESTRUCTION! 🔥"
        elif best_score > 1000:
            strategy = "⚔️ DEVASTATING ATTACK! ⚔️\n💀 PREPARE FOR DOOM! 💀"
        elif best_score > 500:
            strategy = "🔥 CRUSHING ASSAULT! 🔥\n⚡ OVERWHELMING FORCE! ⚡"
        elif best_score > 200:
            strategy = "⚔️ FIERCE STRIKE! ⚔️\n🎯 TACTICAL DOMINATION! 🎯"
        elif best_score > 100:
            strategy = "🔥 AGGRESSIVE PRESSURE! 🔥\n👹 HUNTING FOR BLOOD! 👹"
        elif best_score > 0:
            strategy = "🎯 BUILDING ATTACK! 🎯\n😈 PLOTTING DESTRUCTION! 😈"
        elif best_score > -200:
            strategy = "💪 FIGHTING BACK! 💪\n🔥 COUNTERATTACK MODE! 🔥"
        elif best_score > -500:
            strategy = "🛡️ DEFENSIVE STRIKE! 🛡️\n⚔️ NEVER SURRENDER! ⚔️"
        else:
            strategy = "💀 BERSERK MODE! 💀\n🔥 CHAOS AND DESTRUCTION! 🔥"
    
    think_time = time.time() - start_time
    nps = nodes_searched / max(think_time, 0.001)  # Nodes per second
    
    print(f"🎯 DESTROYER CHOICE: {best_move.uci()} (score: {best_score})")
    print(f"⏱️ Time: {think_time:.1f}s | Nodes: {nodes_searched} | NPS: {nps:.0f}")
    
    # Show alternative moves
    if len(ordered_moves) > 1:
        print("🧠 Top alternatives considered:")
        for i, move in enumerate(ordered_moves[:3]):
            if move != best_move:
                move_type = "CAP" if board.is_capture(move) else "MOV"
                print(f"   {i+1}. {move_type} {move.uci()}")
    
    return best_move, strategy

def get_possible_moves(board, square):
    moves = []
    for move in board.legal_moves:
        if move.from_square == square:
            moves.append(move.to_square)
    return moves

def get_captured_pieces(board):
    captured = {'white': [], 'black': []}
    
    piece_count = {
        'white': {'p': 0, 'r': 0, 'n': 0, 'b': 0, 'q': 0, 'k': 0},
        'black': {'p': 0, 'r': 0, 'n': 0, 'b': 0, 'q': 0, 'k': 0}
    }
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            color = 'white' if piece.color == chess.WHITE else 'black'
            piece_count[color][piece.symbol().lower()] += 1
    
    starting_counts = {'p': 8, 'r': 2, 'n': 2, 'b': 2, 'q': 1, 'k': 1}
    piece_symbols = {'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'}
    
    for color in ['white', 'black']:
        for piece_type, start_count in starting_counts.items():
            current_count = piece_count[color][piece_type]
            captured_count = start_count - current_count
            if captured_count > 0:
                symbol = piece_symbols.get(piece_type, piece_type.upper())
                captured[color].extend([symbol] * captured_count)
    
    return captured

def get_threatened_squares(board):
    """Enhanced threat detection with danger levels"""
    threatened = []
    danger_levels = {}
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == chess.BLACK:
            try:
                attacked_squares = list(board.attacks(square))
                for attacked in attacked_squares:
                    target = board.piece_at(attacked)
                    if target and target.color == chess.WHITE:
                        threatened.append(attacked)
                        
                        # Calculate danger level based on attacking piece
                        if piece.piece_type == chess.QUEEN:
                            danger_levels[attacked] = danger_levels.get(attacked, 0) + 4
                        elif piece.piece_type == chess.ROOK:
                            danger_levels[attacked] = danger_levels.get(attacked, 0) + 3
                        elif piece.piece_type in [chess.BISHOP, chess.KNIGHT]:
                            danger_levels[attacked] = danger_levels.get(attacked, 0) + 2
                        else:
                            danger_levels[attacked] = danger_levels.get(attacked, 0) + 1
            except:
                continue
    
    return threatened, danger_levels

def handle_difficulty_change(key):
    difficulty_map = {
        pygame.K_1: 'Easy',
        pygame.K_2: 'Medium', 
        pygame.K_3: 'Hard',
        pygame.K_4: 'Expert',
        pygame.K_5: 'Goat'
    }
    return difficulty_map.get(key)

# AI thinking thread to prevent UI freezing
ai_move_result = {'move': None, 'strategy': None, 'thinking': False}

def ai_think_thread(board, difficulty):
    """DESTROYER AI thinking thread"""
    global ai_move_result
    ai_move_result['thinking'] = True
    try:
        move, strategy = get_best_move(board.copy(), difficulty)
        ai_move_result['move'] = move
        ai_move_result['strategy'] = strategy
    except Exception as e:
        print(f"🔥 DESTROYER AI error: {e}")
        moves = list(board.legal_moves)
        if moves:
            # Even emergency moves are aggressive
            captures = [m for m in moves if board.is_capture(m)]
            checks = []
            for m in moves:
                board.push(m)
                if board.is_check():
                    checks.append(m)
                board.pop()
            
            if captures:
                ai_move_result['move'] = random.choice(captures)
                ai_move_result['strategy'] = "EMERGENCY DESTRUCTION! 💀"
            elif checks:
                ai_move_result['move'] = random.choice(checks)
                ai_move_result['strategy'] = "EMERGENCY CHECK ATTACK! ⚔️"
            else:
                ai_move_result['move'] = random.choice(moves)
                ai_move_result['strategy'] = "BACKUP DESTRUCTION! 🔥"
    finally:
        ai_move_result['thinking'] = False

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("CHESS AI")
    
    try:
        images = load_images()
    except Exception as e:
        print(f"❌ Error loading images: {e}")
        pygame.quit()
        return
    
    clock = pygame.time.Clock()
    global transposition_table, ai_move_result, killer_moves, history_table

    # Game state
    board = chess.Board()
    move_history = [board.copy()]
    running = True
    selected_square = None
    possible_moves = []
    difficulty = 'Goat'  # Start with GOAT MODE by default!
    game_status = "Your turn (White)"
    captured_pieces = {'white': [], 'black': []}
    last_move = None
    current_eval = 0.0
    ai_thinking_time = 0.0
    ai_strategy = "💀 GOAT MODE ACTIVATED! 💀\n🔥 PREPARE FOR ANNIHILATION! 🔥"
    threatened_squares = []
    danger_levels = {}
    ai_thread = None
    ai_depth = DIFFICULTY_SETTINGS[difficulty]['depth']

    print("🔥💀🔥💀🔥💀 ULTIMATE DESTROYER CHESS AI ACTIVATED! 💀🔥💀🔥💀")
    print(f"👹 Current Level: {difficulty} - AI WILL SHOW ABSOLUTE NO MERCY!")
    print("⚔️ This AI is programmed for TOTAL DOMINATION and DESTRUCTION!")
    print("💀 Enhanced with ALL advanced chess engine techniques!")
    print("🎯 Features: 9-depth search, quiescence, iterative deepening, killer moves!")
    print("🔥 WARNING: Even 'Easy' mode will CRUSH most players!")
    print("💀 GOAT MODE: Prepare to witness chess perfection!")
    print("📋 Controls: Mouse=Move, R=Restart, U=Undo, 1-5=Difficulty, Q=Quit")

    while running:
        try:
            move_count = len(board.move_stack)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    new_difficulty = handle_difficulty_change(event.key)
                    if new_difficulty:
                        difficulty = new_difficulty
                        ai_depth = DIFFICULTY_SETTINGS[difficulty]['depth']
                        transposition_table.clear()
                        killer_moves.clear()
                        history_table.clear()
                        
                        aggression = DIFFICULTY_SETTINGS[difficulty]['aggression']
                        tactical = DIFFICULTY_SETTINGS[difficulty]['tactical_bonus']
                        
                        print(f" Difficulty changed to {difficulty} ")
                        print(f" Aggression: {aggression}x | Tactical: {tactical}x | Depth: {ai_depth}")
                        
                        if difficulty == 'Goat':
                            print("GOAT MODE: ULTIMATE DESTRUCTION PROTOCOL!")
                            ai_strategy = " GOAT MODE ACTIVATED! \n YOUR DOOM IS INEVITABLE! "
                        elif difficulty == 'Expert':
                            print("⚔️⚔️ EXPERT MODE: MAXIMUM DEVASTATION! ⚔️⚔️")
                            ai_strategy = " EXPERT DESTROYER! \n ANNIHILATION IMMINENT! "
                        elif difficulty == 'Hard':
                            print("HARD MODE: BRUTAL DOMINATION!")
                            ai_strategy = " HARD DESTROYER! \n⚔️ CRUSHING EVERYTHING! ⚔️"
                        elif difficulty == 'Medium':
                            print(" MEDIUM MODE: AGGRESSIVE ASSAULT!")
                            ai_strategy = " MEDIUM AGGRESSION! \n HUNTING FOR KILLS! "
                        else:
                            print("EASY MODE: Still DEVASTATINGLY aggressive!")
                            ai_strategy = " EASY DESTROYER! \n NO MERCY EVEN HERE! "
                        continue
                    
                    if event.key == pygame.K_r:
                        print("Restarting... DESTROYER AI hungry for new victim!")
                        board.reset()
                        move_history = [board.copy()]
                        selected_square = None
                        possible_moves = []
                        last_move = None
                        current_eval = 0.0
                        threatened_squares = []
                        danger_levels = {}
                        transposition_table.clear()
                        killer_moves.clear()
                        history_table.clear()
                        ai_move_result = {'move': None, 'strategy': None, 'thinking': False}
                        if ai_thread and ai_thread.is_alive():
                            ai_thread.join(timeout=1.0)
                        
                        # Reset strategy based on difficulty
                        if difficulty == 'GOAT':
                            ai_strategy = "GOAT MODE RESET!\n READY FOR MASSACRE! "
                        else:
                            ai_strategy = f" {difficulty.upper()} DESTROYER READY! \n FRESH BLOOD AWAITS! "
                        
                    elif event.key == pygame.K_q:
                        running = False
                        break
                        
                    elif event.key == pygame.K_u:
                        if not ai_move_result['thinking']:
                            if len(move_history) >= 3:
                                move_history = move_history[:-2]
                                board = move_history[-1].copy()
                                selected_square = None
                                possible_moves = []
                                last_move = None
                                threatened_squares = []
                                danger_levels = {}
                                print("Moves undone - DESTROYER AI still thirsts for blood!")
                            elif len(move_history) >= 2:
                                move_history = move_history[:-1]
                                board = move_history[-1].copy()
                                selected_square = None
                                possible_moves = []
                                last_move = None
                                threatened_squares = []
                                danger_levels = {}
                                print("Move undone - No escape from destruction!")

                elif board.turn == chess.WHITE and event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over() and not ai_move_result['thinking']:
                    x, y = pygame.mouse.get_pos()
                    if x < BOARD_SIZE:
                        col = x // SQUARE_SIZE
                        row = 7 - (y // SQUARE_SIZE)
                        
                        if 0 <= col < 8 and 0 <= row < 8:
                            square = chess.square(col, row)

                            if selected_square is None:
                                piece = board.piece_at(square)
                                if piece and piece.color == chess.WHITE:
                                    selected_square = square
                                    possible_moves = get_possible_moves(board, square)
                                    print(f"Selected: {chess.square_name(square)} ({piece.symbol()}) - Choose your move wisely!")
                            else:
                                move = chess.Move(selected_square, square)
                                
                                piece = board.piece_at(selected_square)
                                if (piece and piece.piece_type == chess.PAWN and 
                                    chess.square_rank(square) == 7):
                                    move = chess.Move(selected_square, square, promotion=chess.QUEEN)
                                
                                if move in board.legal_moves:
                                    move_desc = f"Human move: {move.uci()}"
                                    if board.is_capture(move):
                                        captured_piece = board.piece_at(square)
                                        move_desc += f" (captured {captured_piece.symbol()})"
                                        print(f"{move_desc} - DESTROYER AI will make you PAY DEARLY!")
                                    else:
                                        print(f"{move_desc} - AI plotting your DESTRUCTION... ")
                                    
                                    board.push(move)
                                    move_history.append(board.copy())
                                    last_move = move
                                    
                                    try:
                                        settings = DIFFICULTY_SETTINGS[difficulty]
                                        current_eval = evaluate_board(board, settings['aggression'], settings['tactical_bonus']) / 100.0
                                    except:
                                        current_eval = 0.0
                                    
                                else:
                                    print(f"❌ Illegal move: {move.uci()} - Even your moves can't escape the rules! ❌")
                                
                                selected_square = None
                                possible_moves = []

            # Update enhanced threat visualization
            if board.turn == chess.WHITE:
                threatened_squares, danger_levels = get_threatened_squares(board)
            else:
                threatened_squares = []
                danger_levels = {}

            # Calculate max danger for visualization
            max_danger = max(danger_levels.values()) if danger_levels else 0

            # Draw everything with enhanced visuals
            screen.fill(WHITE)
            draw_board(screen, selected_square, possible_moves, last_move, threatened_squares, max_danger)
            draw_pieces(screen, board, images)
            
            captured_pieces = get_captured_pieces(board)
            
            # Enhanced game status with BRUTAL messaging
            if board.is_game_over():
                if board.is_checkmate():
                    winner = "Black" if board.turn == chess.WHITE else "White"
                    if winner == "Black":
                        game_status = " CHECKMATE!\n DESTROYER AI OBLITERATES YOU! \n TOTAL ANNIHILATION ACHIEVED! \nYOU HAVE BEEN DESTROYED! "
                        ai_strategy = "VICTORY! DOMINATION! \n ANOTHER VICTIM FALLS! "
                    else:
                        game_status = "💥 IMPOSSIBLE CHECKMATE! 💥\n HUMAN DEFEATS GOAT AI! \n🎉 LEGENDARY ACHIEVEMENT! 🎉\n👑 YOU ARE A CHESS GOAT! 👑"
                        ai_strategy = " SYSTEM ERROR... 💀😵\n🤖 HOW DID YOU WIN?! 🤖"
                elif board.is_stalemate():
                    game_status = " STALEMATE! ⚖️\nYou barely survived\nthe DESTROYER'S wrath!\n😤 AI is UNSATISFIED! 😤"
                    ai_strategy = " STALEMATE RAGE! \n VICTORY WAS SO CLOSE! "
                else:
                    game_status = "🤝 DRAW ACHIEVED! 🤝\nYou escaped total\nannihilation... this time!\n😅 Consider yourself lucky! 😅"
                    ai_strategy = "😤⚔️ DRAW ACCEPTED! ⚔️😤\n💀 NEXT TIME: DESTRUCTION! 💀"
                    
            elif board.is_check():
                if board.turn == chess.WHITE:
                    check_severity = "💀💀💀 ULTIMATE CHECK! 💀💀💀" if max_danger >= 3 else "💀 DEVASTATING CHECK! 💀"
                    game_status = f"{check_severity}\nWhite to move\n🔥🔥 YOUR KING IS DOOMED! 🔥🔥\n⚰️ PREPARE FOR CHECKMATE! ⚰️"
                    ai_strategy = "⚔️💀 CHECKMATE INCOMING! 💀⚔️\n🔥 THE END IS NEAR! 🔥"
                else:
                    game_status = f"⚡ Check! ⚡\nBlack to move\n😤 AI temporarily trapped!\n🔥 But still DANGEROUS! 🔥"
                    ai_strategy = "😤💪 TEMPORARY SETBACK! 💪😤\n⚔️ COUNTERATTACK LOADING! ⚔️"
                    
            else:
                if board.turn == chess.WHITE:
                    if ai_move_result['thinking']:
                        thinking_msgs = [
                            "💀 DESTROYER AI calculating your DOOM... 💀\n🧠 Deep analysis in progress... 🧠\n PLOTTING MAXIMUM DESTRUCTION! 🔥",
                            "🎯 AI scanning for WEAKNESSES... 🎯\n⚔️ Tactical combinations loading... ⚔️\n💀 YOUR DEFEAT IS INEVITABLE! 💀",
                            "👹 EVIL GENIUS at work... 👹\n Calculating DEVASTATING moves... \n💀 ANNIHILATION PROTOCOL ACTIVE! 💀"
                        ]
                        game_status = random.choice(thinking_msgs)
                        ai_strategy = f"🧠 DEPTH {ai_depth} ANALYSIS! 🧠\n DESTRUCTION ALGORITHMS! "
                    else:
                        threat_level = len(threatened_squares)
                        if threat_level >= 5:
                            game_status = "⚠️💀 EXTREME DANGER! 💀⚠️\nYour turn (White)\n MULTIPLE PIECES THREATENED! \n DEATH SURROUNDS YOU! "
                        elif threat_level >= 3:
                            game_status = "⚠️ HIGH DANGER! ⚠️\nYour turn (White)\n⚔️ AI has you surrounded! ⚔️\n💀 Choose carefully! 💀"
                        elif threat_level >= 1:
                            game_status = "⚠️⚡ DANGER! ⚡⚠️\nYour turn (White)\n👹 AI is stalking you! 👹\n🎯 Stay alert! 🎯"
                        else:
                            game_status = "🎯 Your turn 🎯\n(White to move)\n💀 AI plotting in shadows... 💀\n⚔️ The calm before storm! ⚔️"
                        
                        # Position analysis for human
                        try:
                            settings = DIFFICULTY_SETTINGS[difficulty]
                            eval_score = evaluate_board(board, settings['aggression'], settings['tactical_bonus'])
                            if eval_score > 500:
                                ai_strategy = "YOU'RE FINISHED! \nTOTAL DOMINATION!"
                            elif eval_score > 200:
                                ai_strategy = "⚔️ CRUSHING YOU! ⚔️👹\n VICTORY IS MINE! "
                            elif eval_score > 100:
                                ai_strategy = "GAINING CONTROL!\n PRESSURE BUILDING! "
                            elif eval_score > -100:
                                ai_strategy = "🎯 BALANCED BATTLE! 🎯\nSEEKING WEAKNESS! "
                            elif eval_score > -200:
                                ai_strategy = "😤 FIGHTING BACK! 😤\n⚔️ NEVER SURRENDER! ⚔️"
                            else:
                                ai_strategy = "🔥 BERSERK MODE! 🔥\n👹 CHAOS UNLEASHED! 👹"
                        except:
                            ai_strategy = "🧠🔍 ANALYZING POSITION... 🔍🧠\n💀 PLOTTING DESTRUCTION! 💀"
                else:
                    game_status = f"🔥💀 DESTROYER AI THINKING... 💀🔥\n🧠 Depth {ai_depth} calculation! 🧠\n⚔️ MAXIMUM AGGRESSION MODE! ⚔️\n👹 YOUR DOOM APPROACHES! 👹"
                    ai_strategy = f"💀🧠 GOAT-LEVEL ANALYSIS! 🧠💀\n🔥 ULTIMATE DESTRUCTION! 🔥"
            
            draw_sidebar(screen, difficulty, game_status, captured_pieces, 
                        current_eval, ai_thinking_time, move_count, ai_strategy, ai_depth)
            pygame.display.flip()

            # Handle AI moves with ULTRA AGGRESSIVE commentary
            if board.turn == chess.BLACK and not board.is_game_over():
                if not ai_move_result['thinking'] and ai_move_result['move'] is None:
                    # Start AI thinking in background
                    settings = DIFFICULTY_SETTINGS[difficulty]
                    aggression = settings['aggression']
                    tactical = settings['tactical_bonus']
                    
                    print(f"💀 DESTROYER AI ACTIVATED! Level: {difficulty} 💀")
                    print(f"👹 Aggression: {aggression}x | Tactical: {tactical}x | Depth: {ai_depth}")
                    print("💀 CALCULATING YOUR ANNIHILATION... 💀")
                    
                    ai_thread = threading.Thread(target=ai_think_thread, args=(board, difficulty))
                    ai_thread.daemon = True
                    ai_thread.start()
                    ai_thinking_start = time.time()
                
                elif not ai_move_result['thinking'] and ai_move_result['move'] is not None:
                    # AI has finished thinking - TIME FOR DESTRUCTION
                    ai_move = ai_move_result['move']
                    strategy = ai_move_result['strategy']
                    ai_thinking_time = time.time() - ai_thinking_start
                    
                    if ai_move and ai_move in board.legal_moves:
                        move_desc = f" DESTROYER STRIKES: {ai_move.uci()}"
                        
                        # Enhanced move description
                        if board.is_capture(ai_move):
                            captured_piece = board.piece_at(ai_move.to_square)
                            if captured_piece:
                                piece_name = {
                                    'p': 'PAWN', 'r': 'ROOK', 'n': 'KNIGHT', 
                                    'b': 'BISHOP', 'q': 'QUEEN', 'k': 'KING'
                                }.get(captured_piece.symbol().lower(), 'PIECE')
                                move_desc += f" ( DESTROYED {piece_name}! )"
                            print(f" {move_desc} | Strategy: {strategy} ")
                        else:
                            # Check if it's a special move
                            if board.is_castling(ai_move):
                                move_desc += " (🏰 FORTRESS MODE)"
                            elif ai_move.promotion:
                                move_desc += f" (👑 PROMOTION TO {'QUEEN' if ai_move.promotion == chess.QUEEN else 'PIECE'}!)"
                            
                            print(f" {move_desc} | Strategy: {strategy} ")
                        
                        # Execute the move
                        board.push(ai_move)
                        move_history.append(board.copy())
                        last_move = ai_move
                        ai_strategy = strategy
                        
                        # Update evaluation
                        try:
                            settings = DIFFICULTY_SETTINGS[difficulty]
                            current_eval = evaluate_board(board, settings['aggression'], settings['tactical_bonus']) / 100.0
                        except:
                            current_eval = 0.0
                        
                        # Enhanced post-move analysis
                        if board.is_check():
                            print("💀⚡ CHECK DELIVERED! Your king trembles in fear! ⚡💀")
                        
                        if board.is_checkmate():
                            print("🏆💀🔥 CHECKMATE! TOTAL DOMINATION ACHIEVED! 🔥💀🏆")
                        
                        # Count threats created
                        new_threats, _ = get_threatened_squares(board)
                        if len(new_threats) >= 3:
                            print(f"👹🔥 AI now threatens {len(new_threats)} of your pieces! TERROR UNLEASHED! 🔥👹")
                        elif len(new_threats) >= 1:
                            print(f"⚔️💀 {len(new_threats)} piece(s) under attack! Danger everywhere! 💀⚔️")
                        
                        # Add dramatic thinking delay
                        min_think_time = DIFFICULTY_SETTINGS[difficulty]['think_time']
                        if ai_thinking_time < min_think_time * 0.5:
                            sleep_time = min_think_time * 0.5 - ai_thinking_time
                            time.sleep(sleep_time)
                            ai_thinking_time += sleep_time
                    
                    else:
                        print("🚨💀 AI SYSTEM ERROR - BACKUP DESTRUCTION PROTOCOL ACTIVATED! 💀🚨")
                        legal_moves = list(board.legal_moves)
                        if legal_moves:
                            # Emergency AI still tries to be aggressive
                            emergency_moves = []
                            
                            # Prioritize captures
                            for move in legal_moves:
                                if board.is_capture(move):
                                    emergency_moves.append((move, 3))
                            
                            # Then checks
                            for move in legal_moves:
                                if not board.is_capture(move):
                                    board.push(move)
                                    if board.is_check():
                                        emergency_moves.append((move, 2))
                                    board.pop()
                            
                            # Finally any move
                            for move in legal_moves:
                                if not any(m[0] == move for m in emergency_moves):
                                    emergency_moves.append((move, 1))
                            
                            # Pick best emergency move
                            emergency_moves.sort(key=lambda x: x[1], reverse=True)
                            ai_move = emergency_moves[0][0]
                            
                            if emergency_moves[0][1] == 3:
                                ai_strategy = "💀🚨 EMERGENCY KILL! 🚨💀"
                            elif emergency_moves[0][1] == 2:
                                ai_strategy = "⚔️🚨 EMERGENCY CHECK! 🚨⚔️"
                            else:
                                ai_strategy = "🔥🚨 EMERGENCY MOVE! 🚨🔥"
                            
                            board.push(ai_move)
                            move_history.append(board.copy())
                            last_move = ai_move
                            print(f"🚨⚔️ EMERGENCY: {ai_move.uci()} | {ai_strategy} ⚔️🚨")
                    
                    # Reset AI state
                    ai_move_result = {'move': None, 'strategy': None, 'thinking': False}
                
                elif ai_move_result['thinking']:
                    # AI is still thinking, show dramatic progress
                    thinking_time = time.time() - ai_thinking_start
                    if thinking_time > 1.0:
                        ai_thinking_time = thinking_time
                        
                        # Show thinking progress messages
                        if thinking_time > 3.0:
                            print("🧠💀 DEEP CALCULATION: Finding your weakest points... 💀🧠")
                        elif thinking_time > 2.0:
                            print("⚔️🔍 TACTICAL SCAN: Analyzing all possibilities... 🔍⚔️")

            clock.tick(60)
            
        except Exception as e:
            print(f"💥🚨 Game loop error: {e} 🚨💥")
            continue

    # Cleanup
    if ai_thread and ai_thread.is_alive():
        ai_thread.join(timeout=2.0)
    
    pygame.quit()
    print("👋💀 Thanks for playing ULTIMATE DESTROYER CHESS AI! 💀👋")
    print("🔥💀 Hope you enjoyed the ABSOLUTE DOMINATION experience! 💀🔥")
    print("⚔️👹 The DESTROYER AI showed its true power! 👹⚔️")
    print("💀🏆 Remember: Even losing to this AI is an honor! 🏆💀")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"💥🚨 Error starting DESTROYER AI: {e} 🚨💥")
        print("📦 Make sure you have required libraries:")
        print("   pip install pygame python-chess")
        print("🔥💀👹 ULTIMATE DESTROYER AI awaits your challenge! 👹💀🔥")


