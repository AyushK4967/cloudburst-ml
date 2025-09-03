import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { crypto } from 'https://deno.land/std@0.168.0/crypto/mod.ts'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface CreateNotebookRequest {
  name: string
  gpu_type: string
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

    const { name, gpu_type }: CreateNotebookRequest = await req.json()

    // Generate unique port for Jupyter
    const port = Math.floor(Math.random() * 1000) + 8888
    const rawToken = crypto.randomUUID()
    
    // Create encryption key from user ID and current time (simple encryption)
    const encoder = new TextEncoder()
    const keyData = await crypto.subtle.importKey(
      'raw',
      encoder.encode(user.id.slice(0, 32).padEnd(32, '0')),
      { name: 'AES-GCM' },
      false,
      ['encrypt']
    )
    
    // Encrypt the token
    const iv = crypto.getRandomValues(new Uint8Array(12))
    const encryptedData = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      keyData,
      encoder.encode(rawToken)
    )
    
    // Encode encrypted token and IV for storage
    const encryptedToken = btoa(String.fromCharCode(...new Uint8Array(encryptedData))) + '.' + btoa(String.fromCharCode(...iv))
    
    // Create hash of token for verification
    const tokenHash = await crypto.subtle.digest('SHA-256', encoder.encode(rawToken))
    const tokenHashHex = Array.from(new Uint8Array(tokenHash)).map(b => b.toString(16).padStart(2, '0')).join('')
    
    // Create notebook record first
    const { data: notebook, error: insertError } = await supabaseClient
      .from('notebooks')
      .insert({
        name,
        gpu_type,
        user_id: user.id,
        status: 'starting',
        jupyter_port: port,
        jupyter_url: `https://jupyter-${user.id.slice(0, 8)}.lovable.app`
      })
      .select()
      .single()

    if (insertError) throw insertError

    // Store encrypted token securely
    const { error: tokenError } = await supabaseClient.rpc('create_notebook_token', {
      p_notebook_id: notebook.id,
      p_encrypted_token: encryptedToken,
      p_token_hash: tokenHashHex
    })

    if (tokenError) {
      console.error('Failed to store notebook token:', tokenError)
      throw new Error('Failed to create secure notebook token')
    }

    // Simulate container creation (in production, this would interact with Docker/K8s)
    console.log(`Creating Jupyter container for notebook ${notebook.id}`)
    console.log(`GPU Type: ${gpu_type}, Port: ${port}`)
    
    // Simulate container startup delay
    setTimeout(async () => {
      const { error: updateError } = await supabaseClient
        .from('notebooks')
        .update({ 
          status: 'running',
          container_id: `container_${notebook.id}`
        })
        .eq('id', notebook.id)

      if (updateError) {
        console.error('Failed to update notebook status:', updateError)
      }
    }, 3000)

    // Log usage
    await supabaseClient
      .from('usage_logs')
      .insert({
        user_id: user.id,
        resource_type: 'notebook',
        resource_id: notebook.id,
        usage_amount: 1,
        cost_amount: gpu_type === 'T4' ? 0 : gpu_type === 'V100' ? 0.5 : 1.2
      })

    return new Response(
      JSON.stringify({ 
        success: true, 
        notebook: {
          ...notebook,
          jupyter_url: `${notebook.jupyter_url}?token=${rawToken}` // Use raw token for immediate access
        }
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )

  } catch (error) {
    console.error('Error creating notebook:', error)
    return new Response(
      JSON.stringify({ 
        error: error.message || 'Failed to create notebook' 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400 
      }
    )
  }
})