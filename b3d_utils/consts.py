PAL = "PALETTEFILES"
SF = "SOUNDFILES"
TEXF = "TEXTUREFILES"
MSKF = "MASKFILES"
BCKF = "BACKFILES"
COL = "COLORS"
MAT = "MATERIALS"
SND = "SOUNDS"

SECTIONS = [PAL, SF, TEXF, MSKF, BCKF, COL, MAT, SND]

PALETTE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Hex to RGB Palette (16x16)</title>
  <style>
    body {
      font-family: sans-serif;
      background-color: #fff;
      color: #000;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }

    .palette {
      display: grid;
      grid-template-columns: repeat(16, 20px);
      grid-template-rows: repeat(16, 20px);
      gap: 2px;
    }

    .color {
      width: 20px;
      height: 20px;
      font-size: 10px;
      display: flex;
      justify-content: center;
      align-items: center;
      box-shadow: 0 0 2px #000;
      color: #000;
    }
	
    .container {
      width: 100%;
      max-width: 1800px;
      margin-left: auto;
      margin-right: auto;
      padding-left: 15px;
      padding-right: 15px;
    }

    .row {
      display: flex;
      flex-wrap: wrap;
      margin-left: -15px;
      margin-right: -15px;
    }

    [class^="col-"] {
      padding: 0.5rem;
      box-sizing: border-box;
    }

    .col {
      flex: 1;
      padding-left: 15px;
      padding-right: 15px;
    }

    .col-1 {
      flex: 0 0 8.3333%;
      max-width: 100%;
    }

    .box {
      background-color: #f0f0f0;
      border: 1px solid #ccc;
      padding: 20px;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="container" id="app">
  <script>
    {data}

    function createHeading(titleText) {
      const row = document.createElement("div");
      row.className = "row";
      const col = document.createElement("div");
      col.className = "col";
      const box = document.createElement("div");
      box.className = "box";
      const heading = document.createElement("h2");
      heading.textContent = titleText;
      box.appendChild(heading);
      col.appendChild(box);
      row.appendChild(col);
      return row;
    }

    function createPALTBody(colors) {
      const row = document.createElement("div");
      row.className = "row";
      const col = document.createElement("div");
      col.className = "col-1";
      const box = document.createElement("div");
      box.className = "box";
      const palette = document.createElement("div");
      palette.className = "palette";
      createPalette(palette, colors)
      box.appendChild(palette);
      col.appendChild(box);
      row.appendChild(col);
      return row;
    }

    function createOPACBody(colorsArr, num) {
      const row = document.createElement("div");
      row.className = "row";
      let step = 100/num;
      for(let i=0; i<num; i++){
        const col = document.createElement("div");
        col.className = "col-1";
        const box = document.createElement("div");
        box.className = "box";
        const heading = document.createElement("h5");
        heading.innerText = Math.round(i*step) + "%-" + Math.round(i*step+step) + "%"
        const palette = document.createElement("div");
        palette.className = "palette";
        createPalette(palette, colorsArr[i])
        box.appendChild(palette);
        palette.appendChild(heading);
        col.appendChild(box);
        row.appendChild(col);
      }
      return row;
    }
    
    function createPalette(palDOM, palValues){
      const totalColors = 256;
      for (let i = 0; i < totalColors; i++) {
        const div = document.createElement('div');
        div.className = 'color';
        if (i < palValues.length) {
          div.style.backgroundColor = palValues[i];
          div.textContent = i;
        } else {
          div.style.backgroundColor = 'transparent';
        }
        
        palDOM.appendChild(div);
      }
    }
    const app = document.getElementById('app');

    {js}
    
  </script>
</body>
</html>
"""