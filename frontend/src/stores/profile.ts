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
  jobUrl?: string       // 104 職缺連結
}

export interface JobSeeker {
  id: string
  name: string
  birthDate: string  // YYYY-MM-DD 格式
  companies: Company[]
}

export interface UserProfile {
  birthDate: string | null  // YYYY-MM-DD 格式
  partners: Partner[]
  companies: Company[]
  jobSeekers: JobSeeker[]
  practitionerLevel: PractitionerLevel
  luckyDayCategories: string[]
}

const DEFAULT_CATEGORIES_PRACTITIONER = ['career', 'medical', 'travel', 'shopping', 'grooming']
const DEFAULT_CATEGORIES_GENERAL = ['career', 'medical', 'travel', 'shopping', 'beauty']

const STORAGE_KEY = 'sukuyodo_profile'

// 從 localStorage 讀取
function loadProfile(): UserProfile {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      // 遷移舊資料：移除不再使用的欄位
      const level: PractitionerLevel = parsed.practitionerLevel || 'none'
      const defaultCats = level !== 'none'
        ? DEFAULT_CATEGORIES_PRACTITIONER
        : DEFAULT_CATEGORIES_GENERAL
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
          memo: c.memo,
          jobUrl: c.jobUrl
        })),
        jobSeekers: (parsed.jobSeekers || []).map((s: JobSeeker) => ({
          id: s.id,
          name: s.name,
          birthDate: s.birthDate,
          companies: (s.companies || []).map((c: Company) => ({
            id: c.id,
            name: c.name,
            foundingDate: c.foundingDate,
            memo: c.memo,
            jobUrl: c.jobUrl
          }))
        })),
        practitionerLevel: level,
        luckyDayCategories: Array.isArray(parsed.luckyDayCategories)
          ? parsed.luckyDayCategories
          : defaultCats
      }
    }
  } catch (e) {
    console.error('載入個人檔案失敗')
  }
  return {
    birthDate: null,
    partners: [],
    companies: [],
    jobSeekers: [],
    practitionerLevel: 'none' as PractitionerLevel,
    luckyDayCategories: DEFAULT_CATEGORIES_GENERAL
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

  // 從 /companies.json 載入推薦公司清單（以 JSON 為準，先清空再匯入）
  async function importCompaniesFromJson(): Promise<number> {
    const res = await fetch('/companies.json')
    if (!res.ok) throw new Error('無法讀取 companies.json')
    const list: Omit<Company, 'id'>[] = await res.json()
    profile.value.companies = list.map(c => ({ ...c, id: crypto.randomUUID() }))
    return list.length
  }

  function addJobSeeker(seeker: Omit<JobSeeker, 'id' | 'companies'>) {
    if (profile.value.jobSeekers.length >= 5) {
      throw new Error('最多只能新增 5 位求職者')
    }
    profile.value.jobSeekers.push({
      ...seeker,
      id: crypto.randomUUID(),
      companies: []
    })
  }

  function removeJobSeeker(id: string) {
    const idx = profile.value.jobSeekers.findIndex(s => s.id === id)
    if (idx !== -1) {
      profile.value.jobSeekers.splice(idx, 1)
    }
  }

  function addCompanyToSeeker(seekerId: string, company: Omit<Company, 'id'>) {
    const seeker = profile.value.jobSeekers.find(s => s.id === seekerId)
    if (!seeker) return
    if (seeker.companies.length >= 20) {
      throw new Error('最多只能新增 20 間公司')
    }
    seeker.companies.push({ ...company, id: crypto.randomUUID() })
  }

  function removeCompanyFromSeeker(seekerId: string, companyId: string) {
    const seeker = profile.value.jobSeekers.find(s => s.id === seekerId)
    if (!seeker) return
    const idx = seeker.companies.findIndex(c => c.id === companyId)
    if (idx !== -1) {
      seeker.companies.splice(idx, 1)
    }
  }

  async function importCompaniesForSeeker(seekerId: string, jsonFile: string): Promise<number> {
    const res = await fetch(`/${jsonFile}`)
    if (!res.ok) throw new Error(`無法讀取 ${jsonFile}`)
    const list: Omit<Company, 'id'>[] = await res.json()
    const seeker = profile.value.jobSeekers.find(s => s.id === seekerId)
    if (!seeker) throw new Error('找不到該求職者')
    seeker.companies = list.map(c => ({ ...c, id: crypto.randomUUID() }))
    return list.length
  }

  function clearProfile() {
    profile.value = {
      birthDate: null,
      partners: [],
      companies: [],
      jobSeekers: [],
      practitionerLevel: 'none',
      luckyDayCategories: DEFAULT_CATEGORIES_GENERAL
    }
  }

  function toggleLuckyCategory(key: string) {
    const cats = profile.value.luckyDayCategories
    const idx = cats.indexOf(key)
    if (idx !== -1) {
      cats.splice(idx, 1)
    } else {
      cats.push(key)
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
    addJobSeeker,
    removeJobSeeker,
    addCompanyToSeeker,
    removeCompanyFromSeeker,
    importCompaniesForSeeker,
    clearProfile,
    toggleLuckyCategory,
    RELATION_TYPES,
    PRACTITIONER_LEVELS
  }
}
