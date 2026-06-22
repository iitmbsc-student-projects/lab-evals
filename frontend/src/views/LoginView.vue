<!--
  LoginView.vue
  Login page for all users. Handles Google Sign-In and backend login.
-->
<template>
  <div
    class="min-h-screen flex items-center justify-center bg-gradient-to-br from-zinc-50 to-zinc-100"
  >
    <div class="bg-white p-10 rounded-xl shadow-xl w-full max-w-md">
      <div class="flex flex-col items-center mb-8">
        <div class="bg-zinc-800 text-white rounded-full p-4 mb-4">
          <svg
            class="w-10 h-10"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
            ></path>
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-zinc-900">Lab Evaluation</h1>
        <p class="text-zinc-600 mt-2 text-center">Sign in with your Google account to continue</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-8">
        <svg
          class="animate-spin h-10 w-10 text-zinc-800 mb-3"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        <p class="text-zinc-600 font-medium">Signing you in...</p>
      </div>

      <!-- Sign In Button -->
      <div v-else class="flex flex-col items-center">
        <!-- Declarative Google Sign-In -->
        <div
          id="g_id_onload"
          :data-client_id="clientId"
          data-auto_prompt="false"
          data-callback="onGoogleSignIn"
        ></div>

        <div
          class="g_id_signin"
          data-type="standard"
          data-size="large"
          data-theme="outline"
          data-width="320"
          data-logo_alignment="left"
        ></div>
      </div>

      <!-- Error Message -->
      <div
        v-if="error"
        class="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
      >
        <svg
          class="w-5 h-5 text-red-600 shrink-0 mt-0.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          ></path>
        </svg>
        <div>
          <h3 class="text-sm font-medium text-red-800">Sign in failed</h3>
          <p class="text-sm text-red-700 mt-1">{{ error }}</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="mt-8 pt-6 border-t border-zinc-200 text-center">
        <p class="text-xs text-zinc-500">
          If you do not see the Google Sign-In button, please reload the page, and ensure
          third-party cookies are enabled in your browser.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { loginWithIdToken, fetchMe } from '../api/auth'
import { useAuthStore } from '../store/auth'

const loading = ref(false)
const error = ref('')
const router = useRouter()
const auth = useAuthStore()

// MUST be a plain string (used in template binding)
const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

/**
 * IMPORTANT:
 * Google expects the callback to be a GLOBAL function.
 * With <script setup>, we must explicitly attach it to window.
 */
onMounted(() => {
  ;(
    window as Window & { onGoogleSignIn?: (response: { credential?: string }) => void }
  ).onGoogleSignIn = async (response: { credential?: string }) => {
    const idToken = response?.credential
    if (!idToken) {
      error.value = 'No ID token received'
      return
    }

    loading.value = true
    error.value = ''

    try {
      const { access_token } = await loginWithIdToken(idToken)

      auth.token = access_token
      const user = await fetchMe()
      auth.setAuth(access_token, user)

      router.replace('/')
    } catch (e: unknown) {
      console.log(e)
      error.value = e instanceof Error ? e.message : 'Login failed. Please try again.'
      auth.clearAuth()
    } finally {
      loading.value = false
    }
  }
})
</script>
