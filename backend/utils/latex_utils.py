"""
LaTeX  -  LaTeX 

: 
1.  LaTeX  (, ) 
2. LaTeX  MathML
3. MathML  OMML ( PPTX) 
"""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Backend logic
LATEX_ESCAPES = {
    r'\%': '%',
    r'\$': '$',
    r'\&': '&',
    r'\#': '#',
    r'\_': '_',
    r'\{': '{',
    r'\}': '}',
    r'\ ': ' ',
    r'\,': ' ',  # thin space
    r'\;': ' ',  # thick space
    r'\!': '',   # negative thin space
    r'\quad': '  ',
    r'\qquad': '    ',
}

# Backend logic
LATEX_SYMBOLS = {
    # Backend logic
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
    r'\epsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η', r'\theta': 'θ',
    r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ', r'\mu': 'μ',
    r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π', r'\rho': 'ρ',
    r'\sigma': 'σ', r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ',
    r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
    r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
    r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Phi': 'Φ',
    r'\Psi': 'Ψ', r'\Omega': 'Ω',
    # Backend logic
    r'\times': '×', r'\div': '÷', r'\pm': '±', r'\mp': '∓',
    r'\cdot': '·', r'\ast': '∗', r'\star': '☆',
    r'\leq': '≤', r'\le': '≤', r'\geq': '≥', r'\ge': '≥',
    r'\neq': '≠', r'\approx': '≈',
    r'\equiv': '≡', r'\sim': '∼', r'\propto': '∝',
    r'\infty': '∞', r'\partial': '∂', r'\nabla': '∇',
    r'\sum': '∑', r'\prod': '∏', r'\int': '∫',
    r'\sqrt': '√', r'\angle': '∠', r'\degree': '°',
    # Backend logic
    r'\leftarrow': '←', r'\rightarrow': '→', r'\leftrightarrow': '↔',
    r'\Leftarrow': '⇐', r'\Rightarrow': '⇒', r'\Leftrightarrow': '⇔',
    # Backend logic
    r'\dots': '…', r'\ldots': '…', r'\cdots': '⋯', r'\vdots': '⋮',
    r'\forall': '∀', r'\exists': '∃', r'\in': '∈', r'\notin': '∉',
    r'\subset': '⊂', r'\supset': '⊃', r'\cup': '∪', r'\cap': '∩',
}

# Backend logic
SUPERSCRIPT_MAP = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
    'n': 'ⁿ', 'i': 'ⁱ',
}

# Backend logic
SUBSCRIPT_MAP = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
    'a': 'ₐ', 'e': 'ₑ', 'o': 'ₒ', 'x': 'ₓ',
    'i': 'ᵢ', 'j': 'ⱼ', 'n': 'ₙ', 'm': 'ₘ',
}


def is_simple_latex(latex: str) -> bool:
    """
     LaTeX () 
    
     LaTeX : 
    -  ( 10\%) 
    -  ( \alpha) 
    -  ( x^2, x_1) 
    """
    # Backend logic
    test = latex
    
    # Backend logic
    for escape in LATEX_ESCAPES:
        test = test.replace(escape, '')
    
    # Backend logic
    for symbol in LATEX_SYMBOLS:
        test = test.replace(symbol, '')
    
    # Backend logic
    test = re.sub(r'\^{[^{}]*}', '', test)
    test = re.sub(r'\^[0-9a-zA-Z]', '', test)
    
    # Backend logic
    test = re.sub(r'_{[^{}]*}', '', test)
    test = re.sub(r'_[0-9a-zA-Z]', '', test)
    
    # Backend logic
    remaining = test.strip()
    # Backend logic
    if '\\' in remaining and not remaining.replace('\\', '').isalnum():
        return False
    
    return True


def latex_to_text(latex: str) -> str:
    """
     LaTeX  Unicode 
    
    Args:
        latex: LaTeX 
    
    Returns:
        
    """
    result = latex
    
    # Backend logic
    for escape, char in LATEX_ESCAPES.items():
        result = result.replace(escape, char)
    
    # Backend logic
    for symbol, char in LATEX_SYMBOLS.items():
        result = result.replace(symbol, char)
    
    # Backend logic
    def convert_superscript(match):
        content = match.group(1) if match.group(1) else match.group(2)
        return ''.join(SUPERSCRIPT_MAP.get(c, c) for c in content)
    
    result = re.sub(r'\^{([^{}]*)}|\^([0-9a-zA-Z])', convert_superscript, result)
    
    # Backend logic
    def convert_subscript(match):
        content = match.group(1) if match.group(1) else match.group(2)
        return ''.join(SUBSCRIPT_MAP.get(c, c) for c in content)
    
    result = re.sub(r'_{([^{}]*)}|_([0-9a-zA-Z])', convert_subscript, result)
    
    # Backend logic
    result = re.sub(r'\\(?:text|mathrm|mathbf|mathit|mathbb|mathcal){([^{}]*)}', r'\1', result)
    
    # Backend logic
    result = result.replace('{', '').replace('}', '')
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result


def latex_to_mathml(latex: str) -> Optional[str]:
    """
     LaTeX  MathML
    
    Args:
        latex: LaTeX 
    
    Returns:
        MathML ,  None
    """
    try:
        import latex2mathml.converter
        mathml = latex2mathml.converter.convert(latex)
        return mathml
    except Exception as e:
        logger.warning(f"LaTeX to MathML conversion failed: {e}")
        return None


def mathml_to_omml(mathml: str) -> Optional[str]:
    """
     MathML  OMML (Office Math Markup Language)
    
     Microsoft  MML2OMML.xsl 
    
    Args:
        mathml: MathML 
    
    Returns:
        OMML ,  None
    """
    try:
        from lxml import etree
        import os
        
        # Backend logic
        xsl_path = os.path.join(os.path.dirname(__file__), 'MML2OMML.xsl')
        
        if not os.path.exists(xsl_path):
            logger.warning(f"MML2OMML.xsl not found at {xsl_path}")
            return None
        
        # Backend logic
        mathml_tree = etree.fromstring(mathml.encode('utf-8'))
        
        # Backend logic
        xslt_tree = etree.parse(xsl_path)
        transform = etree.XSLT(xslt_tree)
        
        # Backend logic
        omml_tree = transform(mathml_tree)
        return etree.tostring(omml_tree, encoding='unicode')
    
    except ImportError:
        logger.warning("lxml not installed, cannot convert to OMML")
        return None
    except Exception as e:
        logger.warning(f"MathML to OMML conversion failed: {e}")
        return None


def convert_latex_for_pptx(latex: str) -> Tuple[str, Optional[str]]:
    """
     PPTX  LaTeX 
    
    Args:
        latex: LaTeX 
    
    Returns:
        (text_fallback, omml) 
        - text_fallback:  () 
        - omml: OMML  () 
    """
    # Backend logic
    text_fallback = latex_to_text(latex)
    
    # Backend logic
    if is_simple_latex(latex):
        return text_fallback, None
    
    # Backend logic
    mathml = latex_to_mathml(latex)
    if mathml:
        omml = mathml_to_omml(mathml)
        if omml:
            return text_fallback, omml
    
    return text_fallback, None