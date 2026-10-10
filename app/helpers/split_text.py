# app/utils/split_text.py

import re
from typing import List, Optional
from enum import Enum


class SplitStrategy(str, Enum):
    """Text splitting strategies"""
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    WORD = "word"
    CHARACTER = "character"


def split_text(
    text: str, 
    max_length: int = 1000,
    strategy: SplitStrategy = SplitStrategy.SENTENCE,
    overlap: int = 0
) -> List[str]:
    """
    Split text into chunks of maximum length
    
    Args:
        text: Input text to split
        max_length: Maximum length of each chunk
        strategy: Splitting strategy to use
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    if len(text) <= max_length:
        return [text.strip()]
    
    if strategy == SplitStrategy.SENTENCE:
        return _split_by_sentence(text, max_length, overlap)
    elif strategy == SplitStrategy.PARAGRAPH:
        return _split_by_paragraph(text, max_length, overlap)
    elif strategy == SplitStrategy.WORD:
        return _split_by_word(text, max_length, overlap)
    else:
        return _split_by_character(text, max_length, overlap)


def _split_by_sentence(text: str, max_length: int, overlap: int = 0) -> List[str]:
    """
    Split text by sentences (., !, ?)
    
    Args:
        text: Input text
        max_length: Maximum chunk length
        overlap: Overlap between chunks
        
    Returns:
        List of sentence-based chunks
    """
    # Split by sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Ensure sentence ends with punctuation
        if sentence and sentence[-1] not in '.!?':
            sentence += '.'
        
        # If adding this sentence exceeds max_length, start new chunk
        if len(current_chunk) + len(sentence) + 1 > max_length and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Add overlap
            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + " " + sentence
            else:
                current_chunk = sentence
        else:
            current_chunk += (" " + sentence if current_chunk else sentence)
    
    # Add last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Handle any chunks that are still too long
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_length:
            final_chunks.extend(_split_by_word(chunk, max_length, overlap))
        else:
            final_chunks.append(chunk)
    
    return final_chunks


def _split_by_paragraph(text: str, max_length: int, overlap: int = 0) -> List[str]:
    """
    Split text by paragraphs
    
    Args:
        text: Input text
        max_length: Maximum chunk length
        overlap: Overlap between chunks
        
    Returns:
        List of paragraph-based chunks
    """
    # Split by double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        # If adding this paragraph exceeds max_length, start new chunk
        if len(current_chunk) + len(paragraph) + 2 > max_length and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Add overlap
            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + "\n\n" + paragraph
            else:
                current_chunk = paragraph
        else:
            current_chunk += ("\n\n" + paragraph if current_chunk else paragraph)
    
    # Add last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def _split_by_word(text: str, max_length: int, overlap: int = 0) -> List[str]:
    """
    Split text by words
    
    Args:
        text: Input text
        max_length: Maximum chunk length
        overlap: Overlap between chunks
        
    Returns:
        List of word-based chunks
    """
    words = text.split()
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1  # +1 for space
        
        if current_length + word_length > max_length and current_chunk:
            # Save current chunk
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
            
            # Add overlap
            if overlap > 0:
                # Keep last N characters from previous chunk
                overlap_words = []
                overlap_length = 0
                for w in reversed(current_chunk):
                    if overlap_length + len(w) + 1 <= overlap:
                        overlap_words.insert(0, w)
                        overlap_length += len(w) + 1
                    else:
                        break
                
                current_chunk = overlap_words + [word]
                current_length = sum(len(w) + 1 for w in current_chunk)
            else:
                current_chunk = [word]
                current_length = len(word) + 1
        else:
            current_chunk.append(word)
            current_length += word_length
    
    # Add last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


def _split_by_character(text: str, max_length: int, overlap: int = 0) -> List[str]:
    """
    Split text by character (simple fixed-length split)
    
    Args:
        text: Input text
        max_length: Maximum chunk length
        overlap: Overlap between chunks
        
    Returns:
        List of character-based chunks
    """
    chunks = []
    
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + max_length, text_length)
        chunk = text[start:end]
        chunks.append(chunk.strip())
        
        # Move start position, accounting for overlap
        start = end - overlap if overlap > 0 else end
    
    return chunks


def split_text_for_tts(
    text: str, 
    max_chars: int = 1000,
    preserve_sentences: bool = True
) -> List[str]:
    """
    Specialized split for TTS (optimized for speech synthesis)
    
    Args:
        text: Input text
        max_chars: Maximum characters per chunk
        preserve_sentences: Whether to preserve sentence boundaries
        
    Returns:
        List of TTS-optimized text chunks
    """
    if not text:
        return []
    
    if len(text) <= max_chars:
        return [text.strip()]
    
    if preserve_sentences:
        # Split by sentences first
        chunks = []
        
        # Find all sentence boundaries
        sentence_endings = re.finditer(r'[.!?]+[\s\n]*(?=[A-Z0-9"\'\({\[]|$)', text)
        sentence_starts = [0]
        sentence_ends = []
        
        for match in sentence_endings:
            sentence_ends.append(match.end())
            sentence_starts.append(match.end())
        
        sentence_starts = sentence_starts[:-1]  # Remove last empty start
        
        # Group sentences into chunks
        current_chunk = ""
        for i in range(len(sentence_starts)):
            sentence = text[sentence_starts[i]:sentence_ends[i]].strip()
            
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += (" " + sentence if current_chunk else sentence)
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If sentence itself is too long, split it
                if len(sentence) > max_chars:
                    chunks.extend(_split_long_sentence(sentence, max_chars))
                    current_chunk = ""
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    else:
        # Simple character-based split
        return _split_by_character(text, max_chars, overlap=50)


def _split_long_sentence(sentence: str, max_chars: int) -> List[str]:
    """
    Split a long sentence into smaller parts
    
    Args:
        sentence: Long sentence
        max_chars: Maximum characters per chunk
        
    Returns:
        List of sentence chunks
    """
    # Try to split by commas first
    parts = re.split(r',\s*', sentence)
    
    chunks = []
    current_chunk = ""
    
    for part in parts:
        if len(current_chunk) + len(part) + 2 <= max_chars:
            current_chunk += (", " + part if current_chunk else part)
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            if len(part) > max_chars:
                # Split by words as last resort
                chunks.extend(_split_by_word(part, max_chars, overlap=0))
                current_chunk = ""
            else:
                current_chunk = part
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def estimate_chunks(text: str, max_length: int = 1000) -> int:
    """
    Estimate number of chunks needed for text
    
    Args:
        text: Input text
        max_length: Maximum chunk length
        
    Returns:
        Estimated number of chunks
    """
    if not text:
        return 0
    
    text_length = len(text)
    if text_length <= max_length:
        return 1
    
    # Rough estimate assuming average sentence length
    avg_sentence_length = 100
    num_sentences = text_length // avg_sentence_length + 1
    sentences_per_chunk = max_length // avg_sentence_length
    
    return max(1, num_sentences // sentences_per_chunk + 1)


def get_chunk_info(text: str, max_length: int = 1000) -> dict:
    """
    Get information about text chunks
    
    Args:
        text: Input text
        max_length: Maximum chunk length
        
    Returns:
        Dictionary with chunk information
    """
    chunks = split_text_for_tts(text, max_length)
    
    chunk_lengths = [len(chunk) for chunk in chunks]
    
    return {
        "total_chunks": len(chunks),
        "total_characters": len(text),
        "avg_chunk_size": sum(chunk_lengths) / len(chunks) if chunks else 0,
        "min_chunk_size": min(chunk_lengths) if chunks else 0,
        "max_chunk_size": max(chunk_lengths) if chunks else 0,
        "chunks": chunks
    }


# Convenience function for TTS
def prepare_text_for_tts(
    text: str, 
    max_chunk_size: int = 1000,
    clean_text: bool = True
) -> List[str]:
    """
    Prepare text for TTS processing
    
    Args:
        text: Input text
        max_chunk_size: Maximum characters per chunk
        clean_text: Whether to clean the text (remove extra whitespace, etc.)
        
    Returns:
        List of prepared text chunks
    """
    if clean_text:
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
    
    # Split into chunks optimized for TTS
    chunks = split_text_for_tts(text, max_chunk_size, preserve_sentences=True)
    
    # Final cleanup of each chunk
    cleaned_chunks = []
    for chunk in chunks:
        # Remove extra spaces
        chunk = re.sub(r'\s+', ' ', chunk)
        # Ensure chunk ends with proper punctuation
        if chunk and chunk[-1] not in '.!?':
            chunk += '.'
        cleaned_chunks.append(chunk)
    
    return cleaned_chunks