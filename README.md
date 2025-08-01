# Hard-Truck-1-2-Cli-Tools
Набор Python скриптов для работы с форматами из Hard Truck: Road to Victory и Hard Truck 2, собранные вместе в b3d_tools/b3d_cli.py

Доступны следующие команды:
* Разбиение b3d на подфайлы. Вывод выбранных нод в отдельный файл. (**b3d extract**)
* Извлечение отдельных секций или ресурсов из res файла. (**res extract**)
* Обьединение нескольких b3d или res файлов. (**merge**)
* Удаление отдельных ресурсов из res/нод из b3d. (**remove**)
* Вывод информации о b3d или res файле. (**list**)
* Распаковка и упаковка res файлов(картинки в формате TGA 32-bit) (**pack, unpack**)

Примеры вызова находятся в examples.

Больше информации о форматах:
https://rernr.github.io/RNRDocs/docs/b3D-File-Format/

### Благодарности
-  [Voron295](https://github.com/Voron295)
-  [AlexKimov](https://github.com/AlexKimov)
-  [aleko2144](https://github.com/aleko2144)
-  [link](https://github.com/Duude92)


---
# Command list

## `res` Commands — Manage `.res` Files

### `res extract`

Extracts selected sections or records from a `.res` file into a new file.

**Parameters:**

* `--i` *(required)*: Path to input `.res` file.
* `--sections`: Sections to extract. Default is all.
* `--o`: Output `.res` file path. Defaults to `{name}_extract.res`.

**Include/Reference Filtering:**

* `--inc-soundfiles`, `--inc-backfiles`, `--inc-maskfiles`, `--inc-texturefiles`, `--inc-materials`, `--inc-sounds`: Include specific resources.
* `--ref-soundfiles`, `--ref-maskfiles`, `--ref-texturefiles`: Include only referenced files of corresponding types.

---

### `res list`

Lists all resources in a `.res` file.

**Parameters:**

* `--i` *(required)*: Path to input `.res` file.
* `--o`: Output file path. If omitted, prints to terminal.

---

### `res merge`

Merges two `.res` files.

**Parameters:**

* `--i-from` *(required)*: Path to source `.res` file.
* `--i-to` *(required)*: Path to destination `.res` file.
* `--replace`: Replace existing resources with same names.
* `--o`: Output `.res` file. Default is in-place merge.

---

### `res remove`

Removes specified resources from a `.res` file.

**Parameters:**

* `--i` *(required)*: Path to input `.res` file.
* `--o`: Output `.res` file. Defaults to overwriting input.

**Remove/Reference Filtering:**

* `--rem-soundfiles`, `--rem-backfiles`, `--rem-maskfiles`, `--rem-texturefiles`, `--rem-materials`, `--rem-sounds`: Specific resources to remove.
* `--ref-soundfiles`, `--ref-maskfiles`, `--ref-texturefiles`: Remove only referenced resources of corresponding types.

---

### `res unpack`

Unpacks a `.res` file into its components.

**Parameters:**

* `--i` *(required)*: Path to `.res` file.
* `--o`: Output folder path. Defaults to input path.
* `--sections`: Sections to unpack. Default is all.
* `--tga-debug`: Save `.tga` debug files.

---

### `res pack`

Packs a folder structure back into a `.res` file.

**Parameters:**

* `--i` *(required)*: Path to unpacked folder.
* `--o`: Output `.res` file path. Defaults to folder name.
* `--tga-debug`: Save `.tga` debug files.

---

## `b3d` Commands — Manage `.b3d` Files

### `b3d extract`

Extracts nodes from `.b3d` file with optional connected `.res` resources.

**Parameters:**

* `--i` *(required)*: Path to `.b3d` file.
* `--inc-nodes`: Nodes to extract. Comma-separated string or file path prefixed with `@`.
* `--node-refs`: Include all referenced nodes.
* `--split`: Export each node to separate file.
* `--o`: Output file/folder path.
* `--res`: Path to `.res` file for exporting associated resources.
* `--ref-materials`: Include only used materials.

**Resource Filtering (if `--res` is used):**
Same as in `res extract` command.

---

### `b3d list`

Lists information about `.b3d` file content.

**Parameters:**

* `--i` *(required)*: Path to `.b3d` file.
* `--t` *(required)*: Type of info (`MATERIALS`, `ROOTS`, or `FULL`).
* `--o`: Output file path. Prints to terminal if omitted.

---

### `b3d remove`

Removes specified nodes from `.b3d` file.

**Parameters:**

* `--i` *(required)*: Path to `.b3d` file.
* `--rem-nodes`: Comma-separated node names or file with names prefixed by `@`.
* `--rem-materials`: Material names to remove.
* `--o`: Output file. Defaults to overwriting original.

---

### `b3d merge`

Merges two `.b3d` files.

**Parameters:**

* `--i-from` *(required)*: Path to source `.b3d` file.
* `--i-to` *(required)*: Path to target `.b3d` file.
* `--replace`: Replace existing nodes.
* `--o`: Output `.b3d` file. Defaults to in-place merge.