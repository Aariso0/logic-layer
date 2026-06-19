# Layer 2 of the verification pipeline.
# Searches whitelisted trusted sources; falls back to *.gov domain search
# for the relevant keyword if no whitelisted result matches.
# Uses requests + BeautifulSoup for fetch/parse.