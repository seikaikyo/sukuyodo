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

export type PractitionerLevel = 'none' | 'tokudo' | 'ajari'

export const PRACTITIONER_LEVELS: { value: PractitionerLevel; label: string }[] = [
  { value: 'none', label: '一般' },
  { value: 'tokudo', label: '得度' },
  { value: 'ajari', label: '阿闍梨' },
]

export interface Company {
  id: string
  name: string
  foundingDate: string  // YYYY-MM-DD 格式
  memo?: string
}

export interface UserProfile {
  birthDate: string | null  // YYYY-MM-DD 格式
  partners: Partner[]
  companies: Company[]
  practitionerLevel: PractitionerLevel
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
        })),
        companies: (parsed.companies || []).map((c: Company) => ({
          id: c.id,
          name: c.name,
          foundingDate: c.foundingDate,
          memo: c.memo
        })),
        practitionerLevel: parsed.practitionerLevel || 'none'
      }
    }
  } catch (e) {
    console.error('載入個人檔案失敗')
  }
  return {
    birthDate: null,
    partners: [],
    companies: [],
    practitionerLevel: 'none' as PractitionerLevel
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

  function addCompany(company: Omit<Company, 'id'>) {
    if (profile.value.companies.length >= 20) {
      throw new Error('最多只能新增 20 間公司')
    }
    profile.value.companies.push({
      ...company,
      id: crypto.randomUUID()
    })
  }

  function updateCompany(id: string, updates: Partial<Omit<Company, 'id'>>) {
    const company = profile.value.companies.find(c => c.id === id)
    if (company) {
      Object.assign(company, updates)
    }
  }

  function removeCompany(id: string) {
    const idx = profile.value.companies.findIndex(c => c.id === id)
    if (idx !== -1) {
      profile.value.companies.splice(idx, 1)
    }
  }

  // 從 /companies.json 載入推薦公司清單，新增或更新既有資料
  async function importCompaniesFromJson(): Promise<number> {
    const res = await fetch('/companies.json')
    if (!res.ok) throw new Error('無法讀取 companies.json')
    const list: Omit<Company, 'id'>[] = await res.json()
    let changed = 0
    for (const c of list) {
      const existing = profile.value.companies.find(e => e.name === c.name)
      if (existing) {
        // 更新 memo 和 foundingDate
        if (existing.memo !== c.memo || existing.foundingDate !== c.foundingDate) {
          existing.memo = c.memo
          existing.foundingDate = c.foundingDate
          changed++
        }
      } else if (profile.value.companies.length < 20) {
        profile.value.companies.push({ ...c, id: crypto.randomUUID() })
        changed++
      }
    }
    return changed
  }

  function clearProfile() {
    profile.value = {
      birthDate: null,
      partners: [],
      companies: [],
      practitionerLevel: 'none'
    }
  }

  const isPractitioner = computed(() => profile.value.practitionerLevel !== 'none')

  return {
    profile,
    isProfileSet,
    isPractitioner,
    myBirthDate,
    addPartner,
    updatePartner,
    removePartner,
    addCompany,
    updateCompany,
    removeCompany,
    importCompaniesFromJson,
    clearProfile,
    RELATION_TYPES,
    PRACTITIONER_LEVELS
  }
}
