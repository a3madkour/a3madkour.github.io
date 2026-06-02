\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{madkour-paper}[2026/06/02 Madkour multi-export paper class]

\LoadClass[11pt]{article}

\RequirePackage[utf8]{inputenc}
\RequirePackage{amsmath,amssymb,amsthm}
\RequirePackage{microtype,csquotes,hyperref}
\RequirePackage[backend=biber,style=authoryear]{biblatex}
\RequirePackage{graphicx,listings}

% Theorem-family — shared counter per AMS convention.
\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{claim}[theorem]{Claim}
\newtheorem{conjecture}{Conjecture}
\newtheorem{axiom}{Axiom}

% Definition-style — upright body, bold header.
\theoremstyle{definition}
\newtheorem{definition}{Definition}
\newtheorem{example}{Example}

% Remark-style — upright body, italic header.
\theoremstyle{remark}
\newtheorem{remark}{Remark}
\newtheorem{note}{Note}

% proof — amsthm built-in; auto-appends ∎
