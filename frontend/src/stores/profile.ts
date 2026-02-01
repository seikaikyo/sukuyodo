import { ref, computed, watch } from 'vue'

export type RelationType = 'dating' | 'spouse' | 'parent' | 'family' | 'friend'

export const RELATION_TYPES: { value: RelationType; label: string }[] = [
  { value: 'dating', label: '交往對象' },
  { value: 'spouse', label: '配偶' },
  { value: 'parent', label: '父母' },
  { value: 'family', label: '家人' },
  { value: 'friend', label: '朋友/同事' },
]

export interface Partner {
  id: string
  nickname: string
  birthDate: string  // YYYY-MM-DD 格式
  relation: RelationType
}

export interface UserProfile {
  birthDate: string | null  // YYYY-MM-DD 格式
  partners: Partner[]
}

const STORAGE_KEY = 'sukuyodo_profile'

// 從 localStorage 讀取
function loadProfile(): UserProfile {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      // 遷移舊資料：移除不再使用的欄位
      return {
        birthDate: parsed.birthDate || null,
        partners: (parsed.partners || []).map((p: Partner & { gender?: string; isPrimary?: boolean }) => ({
          id: p.id,
          nickname: p.nickname,
          birthDate: p.birthDate,
          relation: p.relation || 'friend'
        }))
      }
    }
  } catch (e) {
    console.error('載入個人檔案失敗')
  }
  return {
    birthDate: null,
    partners: []
  }
}

// 儲存到 localStorage
function saveProfile(profile: UserProfile) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile))
  } catch (e) {
    console.error('儲存個人檔案失敗')
  }
}

// 全域狀態
const profile = ref<UserProfile>(loadProfile())

// 監聽變化自動儲存
watch(profile, (newProfile) => {
  saveProfile(newProfile)
}, { deep: true })

export function useProfile() {
  const isProfileSet = computed(() => {
    return profile.value.birthDate !== null
  })

  const myBirthDate = computed(() => profile.value.birthDate || null)

  function addPartner(partner: Omit<Partner, 'id'>) {
    if (profile.value.partners.length >= 10) {
      throw new Error('最多只能新增 10 個收藏對象')
    }

    const newPartner: Partner = {
      ...partner,
      id: crypto.randomUUID()
    }

    profile.value.partners.push(newPartner)
  }

  function updatePartner(id: string, updates: Partial<Omit<Partner, 'id'>>) {
    const partner = profile.value.partners.find(p => p.id === id)
    if (partner) {
      Object.assign(partner, updates)
    }
  }

  function removePartner(id: string) {
    const idx = profile.value.partners.findIndex(p => p.id === id)
    if (idx !== -1) {
      profile.value.partners.splice(idx, 1)
    }
  }

  function clearProfile() {
    profile.value = {
      birthDate: null,
      partners: []
    }
  }

  return {
    profile,
    isProfileSet,
    myBirthDate,
    addPartner,
    updatePartner,
    removePartner,
    clearProfile,
    RELATION_TYPES
  }
}
