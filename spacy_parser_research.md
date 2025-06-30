# spaCy-Based Resume Parser Research

## Key Insights from Analytics Vidhya Article

### spaCy Advantages for Resume Parsing:
1. **Named Entity Recognition (NER)**: Pre-trained models for extracting entities
2. **Part-of-Speech (POS) Tagging**: Understanding grammatical structure
3. **Rule-based Matching**: Custom patterns for specific information
4. **Speed and Performance**: Fast processing compared to other NLP libraries
5. **Customization**: Ability to train custom models
6. **Integration**: Works well with other ML libraries

### Implementation Approach:
1. **Text Extraction**: Use pdfminer.six for PDF, python-docx for Word
2. **Contact Information**: Regex patterns for phone, email extraction
3. **Skills Extraction**: Custom skill lists and pattern matching
4. **Education**: Pattern matching for degrees and institutions
5. **Name Extraction**: spaCy's NER for PERSON entities
6. **Experience**: Date patterns and job title recognition

### Key Libraries:
- spacy (core NLP)
- pdfminer.six (PDF text extraction)
- python-docx (Word document processing)
- re (regular expressions)
- Custom skill databases

### Implementation Strategy:
1. Create comprehensive skill databases
2. Use spaCy's matcher for pattern-based extraction
3. Implement custom NER models for domain-specific entities
4. Combine rule-based and ML approaches
5. Add confidence scoring for extracted information

