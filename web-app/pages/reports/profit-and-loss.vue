<template>
  <ClientOnly>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div class="mb-12">
        <h1 class="text-4xl md:text-5xl font-display font-bold text-foreground">
          Profit and Loss
        </h1>
        <p class="text-lg text-foreground/90">
          A summary of your income and expenses.
        </p>

        <div class="flex gap-4 items-center print:hidden">
          <Popover class="mt-6" v-model:open="showBeginningDatePicker">
            <PopoverTrigger as-child>
              <Button>From Date: {{ beginningDateFormatted }}</Button>
            </PopoverTrigger>
            <PopoverContent class="w-64">
              <Calendar
                v-model="beginningDate"
                @update:modelValue="
                  showBeginningDatePicker = false;
                  selectDateRange('custom');
                  loadReport();
                "
              >
              </Calendar>
            </PopoverContent>
          </Popover>
          <Popover class="mt-6 ml-4" v-model:open="showToDatePicker">
            <PopoverTrigger as-child>
              <Button>To Date: {{ toDateFormatted }}</Button>
            </PopoverTrigger>
            <PopoverContent class="w-64">
              <Calendar
                v-model="toDate"
                @update:modelValue="
                  showToDatePicker = false;
                  selectDateRange('custom');
                  loadReport();
                "
              >
              </Calendar>
            </PopoverContent>
          </Popover>
          <DropdownMenu class="mt-6 ml-4">
            <DropdownMenuTrigger as-child>
              <Button>{{ selectedDateRangeLabel }}</Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem
                v-for="option in dateRangeOptions"
                :key="option.value"
                @click="selectDateRange(option.value)"
              >
                {{ option.label }}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <h2 class="mt-6 text-2xl font-bold text-foreground">Income</h2>
        <div class="mt-2">
          <div
            v-for="item in incomeItems"
            :key="item.id"
            class="flex justify-between py-2 border-b border-foreground/10"
          >
            <div class="flex gap-4 items-center">
              <Checkbox v-model="item.selected" />
              <input
                v-model="item.envelopeName"
                @blur="
                  updateAlias(
                    item.envelopeId,
                    item.envelopeName,
                    'profit-and-loss',
                  )
                "
              />
            </div>
            <div class="text-foreground">{{ item.amountFormatted }}</div>
          </div>
        </div>
        <h3 class="mt-1">Total Income: {{ totalIncomeFormatted }}</h3>

        <h2 class="mt-6 text-2xl font-bold text-foreground">Expenses</h2>
        <div class="mt-2">
          <div
            v-for="item in expenseItems"
            :key="item.id"
            class="flex justify-between py-2 border-b border-foreground/10"
          >
            <div class="flex gap-4 items-center">
              <Checkbox v-model="item.selected" />
              <input
                v-model="item.envelopeName"
                @blur="
                  updateAlias(
                    item.envelopeId,
                    item.envelopeName,
                    'profit-and-loss',
                  )
                "
              />
            </div>
            <div class="text-foreground">{{ item.amountFormatted }}</div>
          </div>
        </div>
        <h3 class="mt-1">Total Expenses: {{ totalExpensesFormatted }}</h3>
        <h3 class="mt-6 text-2xl font-bold text-foreground">
          Net Profit/Loss:
          {{ netProfitLossFormatted }}
        </h3>
      </div>
    </main>
  </ClientOnly>
</template>

<script setup>
import {
  CalendarDate,
  fromDate,
  getLocalTimeZone,
} from "@internationalized/date";

let { $api, $auth } = useNuxtApp();

let yearBeginning = new Date();
yearBeginning.setMonth(0);
yearBeginning.setDate(1);
yearBeginning.setHours(0, 0, 0, 0);

let showBeginningDatePicker = ref(false);
let beginningDate = ref(fromDate(yearBeginning, getLocalTimeZone()));
let beginningDateFormatted = computed(() => {
  if (!beginningDate.value) return "Select a date";
  let options = { year: "numeric", month: "long", day: "numeric" };
  return new Date(
    beginningDate.value.year,
    beginningDate.value.month - 1,
    beginningDate.value.day,
  ).toLocaleDateString(undefined, options);
});

let showToDatePicker = ref(false);
let toDate = ref(null);
let toDateFormatted = computed(() => {
  if (!toDate.value) return "Today";
  let options = { year: "numeric", month: "long", day: "numeric" };
  return new Date(
    toDate.value.year,
    toDate.value.month - 1,
    toDate.value.day,
  ).toLocaleDateString(undefined, options);
});

let dateRangeOptions = [
  { label: "Year to Date", value: "year-to-date" },
  { label: "This Month", value: "this-month" },
  { label: "Last Month", value: "last-month" },
  { label: "This Quarter", value: "this-quarter" },
  { label: "Last Quarter", value: "last-quarter" },
  { label: "This Year", value: "this-year" },
  { label: "Last Year", value: "last-year" },
  { label: "Custom", value: "custom" },
];

let selectedDateRange = ref("year-to-date");
let selectedDateRangeLabel = computed(() => {
  let option = dateRangeOptions.find(
    (option) => option.value === selectedDateRange.value,
  );
  return option ? option.label : "Custom";
});

function selectDateRange(value) {
  selectedDateRange.value = value;
  let now = new Date();
  let year = now.getFullYear();
  let month = now.getMonth();
  let day = now.getDate();

  switch (value) {
    case "year-to-date":
      beginningDate.value = fromDate(new Date(year, 0, 1), getLocalTimeZone());
      toDate.value = null;
      break;
    case "this-month":
      beginningDate.value = fromDate(
        new Date(year, month, 1),
        getLocalTimeZone(),
      );
      toDate.value = fromDate(new Date(year, month + 1, 0), getLocalTimeZone());
      break;
    case "last-month":
      beginningDate.value = fromDate(
        new Date(year, month - 1, 1),
        getLocalTimeZone(),
      );
      toDate.value = fromDate(new Date(year, month, 0), getLocalTimeZone());
      break;
    case "this-year":
      beginningDate.value = fromDate(new Date(year, 0, 1), getLocalTimeZone());
      toDate.value = null;
      break;
    case "last-year":
      beginningDate.value = fromDate(
        new Date(year - 1, 0, 1),
        getLocalTimeZone(),
      );
      toDate.value = fromDate(new Date(year - 1, 11, 31), getLocalTimeZone());
      break;
    default:
      // Custom or unhandled
      break;
  }

  loadReport();
}

let reportItems = ref([]);
let incomeItems = computed(() => {
  let items = reportItems.value.filter((item) => item.amount >= 0);
  items.sort((a, b) => b.amount - a.amount);
  return items;
});

let totalIncome = computed(() => {
  let total = incomeItems.value.reduce((sum, item) => {
    if (item.selected) {
      return sum + item.amount;
    }
    return sum;
  }, 0);

  return total;
});

let expenseItems = computed(() => {
  let items = reportItems.value.filter((item) => item.amount < 0);
  items.sort((a, b) => a.amount - b.amount);
  return items;
});

let totalExpenses = computed(() => {
  let total = expenseItems.value.reduce((sum, item) => {
    if (item.selected) {
      return sum + item.amount;
    }
    return sum;
  }, 0);

  return total;
});

let totalIncomeFormatted = computed(() => {
  let total = totalIncome.value;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(total);
});

let totalExpensesFormatted = computed(() => {
  let total = totalExpenses.value;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(total);
});

let netProfitLossFormatted = computed(() => {
  let total = totalIncome.value + totalExpenses.value;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(total);
});

async function loadReport() {
  console.log("Loading report...");
  console.log("From:", beginningDate.value);
  console.log("To:", toDate.value);

  let report = await $api(`/reports/profit-and-loss`, {
    method: "GET",
    params: {
      startDate: beginningDate.value.toAbsoluteString(),
      endDate: toDate.value ? toDate.value.toAbsoluteString() : undefined,
    },
  });

  for (let item of report) {
    item.amount = Number(item.amount);
    item.amountFormatted = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(item.amount);
    item.selected = true;
  }

  reportItems.value = report;
}

function updateAlias(envelopeId, alias, reportType) {
  $api(`/reports/aliases/${reportType}/${envelopeId}`, {
    method: "PUT",
    body: {
      alias,
    },
  });
}

onMounted(async () => {
  if ($auth) {
    await loadReport();
  }
});
</script>
