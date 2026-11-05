import {useCallback, useEffect, useRef, useState} from 'react'
export function useResource<T>(loader: () => Promise<T>, refreshMs?: number) {
  const [data, setData] = useState<T | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [updatedAt, setUpdatedAt] = useState<Date | null>(null); const mounted = useRef(true)
  const refresh = useCallback(async () => { setError(''); try { const result = await loader(); if (mounted.current) { setData(result); setUpdatedAt(new Date()) } } catch (reason) { if (mounted.current) setError(reason instanceof Error ? reason.message : 'Request failed') } finally { if (mounted.current) setLoading(false) } }, [loader])
  useEffect(() => { mounted.current = true; void refresh(); const timer = refreshMs ? window.setInterval(() => void refresh(), refreshMs) : undefined; return () => { mounted.current = false; if (timer) window.clearInterval(timer) } }, [loader, refreshMs])
  return {data, loading, error, updatedAt, refresh}
}
