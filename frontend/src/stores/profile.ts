import { ref, computed, watch } from 'vue'

export interface Partner {
  id: string
  nickname: string
  gender: 'male' | 'female' | 'other'
  birthDate: string  // YYYY-MM-DD 格式
  isPrimary: boolean
}

export interface UserProfile {
  gender: 'male' | 'female' | 'other' | null
  birthDate: string | null  // YYYY-MM-DD 格式
  partners: Partner[]
}

const STORAGE_KEY = 'sukuyodo_profile'

// 從 localStorage 讀取
function loadProfile(): UserProfile {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('載入個人檔案失敗')
  }
  return {
    gender: null,
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

export const GENDER_OPTIONS = [
  { value: 'male', label: '男' },
  { value: 'female', label: '女' },
  { value: 'other', label: '其他' }
]

export function useProfile() {
  const isProfileSet = computed(() => {
    return profile.value.gender !== null && profile.value.birthDate !== null
  })

  const myBirthDate = computed(() => profile.value.birthDate || null)

  const primaryPartner = computed(() => {
    return profile.value.partners.find(p => p.isPrimary) || profile.value.partners[0] || null
  })

  function setMyProfile(
    gender: 'male' | 'female' | 'other',
    birthDate: string
  ) {
    profile.value.gender = gender
    profile.value.birthDate = birthDate
  }

  function addPartner(partner: Omit<Partner, 'id'>) {
    if (profile.value.partners.length >= 5) {
      throw new Error('最多只能新增 5 個關注對象')
    }

    const newPartner: Partner = {
      ...partner,
      id: crypto.randomUUID()
    }

    // 如果是第一個，設為主要
    if (profile.value.partners.length === 0) {
      newPartner.isPrimary = true
    }

    profile.value.partners.push(newPartner)
  }

  function removePartner(id: string) {
    const idx = profile.value.partners.findIndex(p => p.id === id)
    if (idx === -1) return

    const partner = profile.value.partners[idx]
    if (!partner) return

    const wasPrimary = partner.isPrimary
    profile.value.partners.splice(idx, 1)

    // 如果移除的是主要對象，設定第一個為主要
    const firstPartner = profile.value.partners[0]
    if (wasPrimary && firstPartner) {
      firstPartner.isPrimary = true
    }
  }

  function setPrimaryPartner(id: string) {
    profile.value.partners.forEach(p => {
      p.isPrimary = p.id === id
    })
  }

  function clearProfile() {
    profile.value = {
      gender: null,
      birthDate: null,
      partners: []
    }
  }

  return {
    profile,
    isProfileSet,
    myBirthDate,
    primaryPartner,
    setMyProfile,
    addPartner,
    removePartner,
    setPrimaryPartner,
    clearProfile
  }
}
