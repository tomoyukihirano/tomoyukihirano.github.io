# Third-party references and notices

## Asano / al-folio design reference

This standalone alternative follows the proportions, typography and publication-page layout of Yuki M. Asano's public website and its al-folio base. The 800 px container, 770 px inner content width, light Roboto typography, right-aligned years, collection controls and compact bibliography rows informed the new presentation. The preview uses the site's existing flower palette and omits publication thumbnails.

- Reference website: https://yukimasano.github.io/
- Reference publications page: https://yukimasano.github.io/publications/
- Reference source: https://github.com/yukimasano/yukimasano.github.io
- Reference license: https://github.com/yukimasano/yukimasano.github.io/blob/master/LICENSE
- al-folio: https://github.com/alshedivat/al-folio

The MIT license below is reproduced in full from the reference repository's `LICENSE`, including its original attribution. The data adapters, standalone page navigation, filtering and waffle-chart renderer were implemented for this project.

### MIT license retained from the Asano reference

The MIT License (MIT)

Copyright (c) 2022 Maruan Al-Shedivat.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Earlier Fukushima design reference

The earlier Fukushima-inspired alternative remains separate. This alternative retains project-authored publication-chart and supporting interface components from that work. Their earlier style references are acknowledged here, and the previously retained MIT notice is preserved for continuity of the referenced style material.

- Fukushima Lab: https://github.com/kenji-fukushima-lab/kenji-fukushima-lab.github.io
- Earlier base theme: https://github.com/george-gca/multi-language-al-folio
- Reviewed Fukushima source commit: `94d43072f18c999a49d1ed12beeb0a38b74534fa`
- License source: https://github.com/kenji-fukushima-lab/kenji-fukushima-lab.github.io/blob/main/LICENSE

### MIT license retained from the earlier reference

The MIT License (MIT)

Copyright (c) 2025 Maruan Al-Shedivat.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Roboto font

Roboto is distributed under the SIL Open Font License, Version 1.1.

Copyright 2011 The Roboto Project Authors (https://github.com/googlefonts/roboto-classic)

- Official font source: https://github.com/google/fonts/blob/main/ofl/roboto/Roboto%5Bwdth,wght%5D.ttf
- Official metadata: https://github.com/google/fonts/blob/main/ofl/roboto/METADATA.pb
- Official license: https://github.com/google/fonts/blob/main/ofl/roboto/OFL.txt
- Full local license: `assets/fonts/OFL.txt`
- Source and conversion details: `assets/fonts/README.md`
- Source/output hashes and verification: `assets/fonts/build-metadata.json`

`font-faces.css` embeds locally generated Latin and Latin-ext WOFF2 subsets of the official Roboto variable font as data URIs. Normal width is fixed at `wdth=100`, and CSS exposes normal weights 300–700. The original copyright and licensing information is retained in the font tables. The build includes the full text of `assets/fonts/OFL.txt` after these notices in the generated HTML. Individual WOFF2 files are not required in Git or at runtime.

## Original website content and project code

The research text, bibliographic records, author information, original images and other user-supplied content are taken from Tomoyuki Hirano's existing public website. Their ownership and existing rights remain with their respective rights holders. These third-party software and font notices do not grant a new license to that content or transfer its ownership.

Research papers, publication figures, profile photographs, profile text, lab membership data, analytics settings and access-request services from the design-reference websites are not included. Their content is not relicensed by this notice. No new license is asserted here for the project's independently written application code.
