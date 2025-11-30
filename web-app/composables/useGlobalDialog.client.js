export function useGlobalDialog() {
  let globalDialog = reactive({
    title: "",
    component: null,
    props: {},
  });

  return {
    dialogState: globalDialog,
    confirmDelete(title, description) {
      globalDialog.title = title;
      globalDialog.component = ConfirmDeleteComponent;
      globalDialog.props = { description };
    },
  };
}
