function triggerDownload(url: string, filename: string) {
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = 'noreferrer';
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
}

export function getFilenameFromUrl(url: string, fallback: string) {
  try {
    const parsedUrl = new URL(url);
    const candidate = parsedUrl.pathname.split('/').pop();

    if (candidate) {
      return decodeURIComponent(candidate);
    }
  } catch {
    return fallback;
  }

  return fallback;
}

export function buildDownloadProxyUrl(url: string, filename: string) {
  const params = new URLSearchParams({
    url,
    filename,
  });

  return `/__download?${params.toString()}`;
}

export async function downloadFromUrl(url: string, filename: string) {
  triggerDownload(buildDownloadProxyUrl(url, filename), filename);
}
