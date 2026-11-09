"""Retrieve the versioned example inputs without replacing the model code."""
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen
import hashlib
import json
import os
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def _inventory(root):
    manifest = json.loads((root / 'example_data.json').read_text())
    records = manifest['files']
    expected = {}
    for record in records:
        name = PurePosixPath(record['path'])
        if name.is_absolute() or '..' in name.parts or not name.parts or name.parts[0] != 'data':
            raise ValueError('Invalid example-data path.')
        if str(name) in expected or int(record['bytes']) < 0:
            raise ValueError('Invalid example-data inventory.')
        expected[str(name)] = int(record['bytes'])
    if not expected:
        raise ValueError('The example-data inventory is empty.')
    return manifest, expected


def ensure_example_data(root=None, archive_path=None):
    """Load the published data once, or use the original tutorial ZIP locally.

    The release archive contains the original verified MSI package. Only its
    data files are installed; the repository's current Python code is retained.
    File names, byte sizes, ZIP CRCs and the bundled lake catalogue are checked.
    """
    root = Path(root).resolve() if root else ROOT
    manifest, expected = _inventory(root)
    if all((root / name).is_file() and (root / name).stat().st_size == size
           for name, size in expected.items()):
        print('Example data are ready.')
        return root / 'data'
    temporary = Path(tempfile.mkdtemp(prefix='.flake_data_', dir=str(root)))
    try:
        if archive_path is not None:
            archive_path = Path(archive_path).expanduser().resolve()
            if not archive_path.is_file():
                raise FileNotFoundError('Example archive not found: ' + str(archive_path))
        else:
            archive_path = temporary / manifest['archive_name']
            print('Downloading the 50-lake example data (about 96 MiB)...')
            request = Request(manifest['url'], headers={'User-Agent': 'FLake-Python-tutorial'})
            try:
                with urlopen(request, timeout=90) as response, archive_path.open('wb') as stream:
                    downloaded = 0
                    for block in iter(lambda: response.read(1024 * 1024), b''):
                        downloaded += len(block)
                        if downloaded > 250 * 1024**2:
                            raise ValueError('The example download is unexpectedly large.')
                        stream.write(block)
            except Exception as exc:
                raise RuntimeError(
                    'The example-data release could not be downloaded. Check the connection '
                    'and that the data-v1.0.0 release contains FLake_Tutorial.zip. '
                    'For a local archive, set LOCAL_DATA_ARCHIVE in the setup cell.'
                ) from exc
        if manifest.get('sha256'):
            digest = hashlib.sha256()
            with archive_path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
            if digest.hexdigest() != manifest['sha256']:
                raise ValueError('The data archive does not match its recorded SHA-256.')
        prefix = manifest['archive_prefix'].rstrip('/') + '/'
        staging = temporary / 'unpacked'
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            if len(infos) > 2500 or sum(info.file_size for info in infos) > 750 * 1024**2:
                raise ValueError('The example archive is unexpectedly large.')
            if len({info.filename for info in infos}) != len(infos):
                raise ValueError('The example archive contains duplicate entries.')
            selected = {}
            for info in infos:
                name = PurePosixPath(info.filename)
                if name.is_absolute() or '..' in name.parts:
                    raise ValueError('The archive contains an invalid path.')
                if info.filename.startswith(prefix + 'data/') and not info.is_dir():
                    selected[info.filename[len(prefix):]] = info
            if set(selected) != set(expected):
                raise ValueError('This ZIP does not contain the expected 50-lake dataset.')
            # Reading every data member to EOF checks its ZIP CRC before files
            # are installed. No Python files from the archive are executed.
            for name, size in expected.items():
                info = selected[name]
                if info.file_size != size:
                    raise ValueError('Data size differs from the verified inventory: ' + name)
                destination = staging / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, destination.open('wb') as target:
                    shutil.copyfileobj(source, target)
            catalogue = root / 'data/lakes.csv'
            if catalogue.exists() and catalogue.read_bytes() != (staging / 'data/lakes.csv').read_bytes():
                raise ValueError('The release and repository lake catalogues differ.')
        for name in expected:
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(str(staging / name), str(destination))
        print('Ready: 50 lakes, historical forcing and four SSP scenarios.')
        return root / 'data'
    finally:
        shutil.rmtree(temporary, ignore_errors=True)
