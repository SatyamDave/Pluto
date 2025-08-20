'use client'

import { SessionProvider } from 'next-auth/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { SWRConfig } from 'swr'
import { useState } from 'react'

interface ProvidersProps {
  children: React.ReactNode
}

export function Providers({ children }: ProvidersProps) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: false,
        staleTime: 5 * 60 * 1000, // 5 minutes
      },
    },
  }))

  return (
    <SessionProvider>
      <QueryClientProvider client={queryClient}>
        <SWRConfig
          value={{
            revalidateOnFocus: false,
            revalidateOnReconnect: true,
            dedupingInterval: 2000,
            errorRetryCount: 3,
          }}
        >
          {children}
        </SWRConfig>
      </QueryClientProvider>
    </SessionProvider>
  )
}
