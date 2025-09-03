import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { crypto } from 'https://deno.land/std@0.168.0/crypto/mod.ts'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface ManageNotebookRequest {
  notebook_id: string
  action: 'start' | 'stop' | 'delete' | 'get_url'
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    )

    const { data: { user } } = await supabaseClient.auth.getUser()
    if (!user) {
      throw new Error('Unauthorized')
    }

    const { notebook_id, action }: ManageNotebookRequest = await req.json()

    // Get notebook details
    const { data: notebook, error: fetchError } = await supabaseClient
      .from('notebooks')
      .select('*')
      .eq('id', notebook_id)
      .eq('user_id', user.id)
      .single()

    if (fetchError || !notebook) {
      throw new Error('Notebook not found')
    }

    switch (action) {
      case 'start':
        if (notebook.status === 'running') {
          throw new Error('Notebook is already running')
        }

        // Update status to starting
        await supabaseClient
          .from('notebooks')
          .update({ status: 'starting' })
          .eq('id', notebook_id)

        // Simulate container start
        console.log(`Starting container ${notebook.container_id}`)
        
        setTimeout(async () => {
          await supabaseClient
            .from('notebooks')
            .update({ status: 'running' })
            .eq('id', notebook_id)
        }, 2000)

        return new Response(
          JSON.stringify({ success: true, message: 'Notebook starting' }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )

      case 'stop':
        if (notebook.status === 'stopped') {
          throw new Error('Notebook is already stopped')
        }

        await supabaseClient
          .from('notebooks')
          .update({ status: 'stopping' })
          .eq('id', notebook_id)

        // Simulate container stop
        console.log(`Stopping container ${notebook.container_id}`)
        
        setTimeout(async () => {
          await supabaseClient
            .from('notebooks')
            .update({ status: 'stopped' })
            .eq('id', notebook_id)
        }, 2000)

        return new Response(
          JSON.stringify({ success: true, message: 'Notebook stopping' }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )

      case 'delete':
        // Stop and remove container
        console.log(`Deleting container ${notebook.container_id}`)
        
        await supabaseClient
          .from('notebooks')
          .delete()
          .eq('id', notebook_id)

        return new Response(
          JSON.stringify({ success: true, message: 'Notebook deleted' }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )

      case 'get_url':
        if (notebook.status !== 'running') {
          throw new Error('Notebook must be running to get URL')
        }

        // Retrieve and decrypt token securely
        const { data: tokenData, error: tokenError } = await supabaseClient.rpc('get_notebook_token', {
          p_notebook_id: notebook_id
        })

        if (tokenError || !tokenData || tokenData.length === 0) {
          throw new Error('Notebook token not found or expired')
        }

        // Decrypt the token
        const [encryptedB64, ivB64] = tokenData[0].encrypted_token.split('.')
        const encrypted = Uint8Array.from(atob(encryptedB64), c => c.charCodeAt(0))
        const iv = Uint8Array.from(atob(ivB64), c => c.charCodeAt(0))
        
        const encoder = new TextEncoder()
        const decoder = new TextDecoder()
        const keyData = await crypto.subtle.importKey(
          'raw',
          encoder.encode(user.id.slice(0, 32).padEnd(32, '0')),
          { name: 'AES-GCM' },
          false,
          ['decrypt']
        )
        
        const decryptedData = await crypto.subtle.decrypt(
          { name: 'AES-GCM', iv },
          keyData,
          encrypted
        )
        
        const token = decoder.decode(decryptedData)
        const jupyterUrl = `${notebook.jupyter_url}?token=${token}`
        
        return new Response(
          JSON.stringify({ 
            success: true, 
            jupyter_url: jupyterUrl,
            port: notebook.jupyter_port,
            expires_at: tokenData[0].expires_at
          }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )

      default:
        throw new Error('Invalid action')
    }

  } catch (error) {
    console.error('Error managing notebook:', error)
    return new Response(
      JSON.stringify({ 
        error: error.message || 'Failed to manage notebook' 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400 
      }
    )
  }
})