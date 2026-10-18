# Windows editable target detection

Research date: 2026-10-18. Scope: an external dictation client detecting the currently editable target in Excel and its Copilot pane. No document contents or screenshots were inspected for this research.

## Findings from Microsoft documentation

- **A control type is not an editability verdict.** A DataItem must expose ValuePattern when its primary text is editable. ValuePattern also applies to editable list and tree items, including outside their current edit mode. Therefore an Edit/ComboBox-only whitelist excludes valid writable targets. Conversely ValuePattern can represent non-text values such as a color picker, so accepting every writable ValuePattern indiscriminately would broaden scope beyond text entry. [DataItem control type](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-supportdataitemcontroltype), [Value control pattern](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-implementingvalue).

- **Inspect capabilities on the actual focused target.** ValuePattern.IsReadOnly and IsEnabled describe whether its value can be changed. TextPattern support alone proves text access, not permission to edit: Microsoft allows it for selectable read-only text and even text on buttons. For TextPattern targets, the IsReadOnly text attribute (40015) describes whether a range can be modified. Unsupported or mixed attribute results need explicit handling; GetAttributeValue can return reserved NotSupported or MixedAttribute values. [Value control pattern](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-implementingvalue), [Text and TextRange patterns](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-implementingtextandtextrange), [Text attributes](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-textattribute-ids), [GetAttributeValue](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextrange-getattributevalue).

- **Resolve focus within a bounded container.** GetFocusedElement retrieves input focus, but Microsoft also documents inspecting children/descendants of the focused element. FindFirst searches from a specified root and condition; Microsoft recommends starting from a lower container to avoid traversing hundreds or thousands of elements. HasKeyboardFocus (30008) means current focus; IsKeyboardFocusable means only that an element *can* accept focus. Provider errors/races remain possible: GetFocusedElement may return ELEMENTNOTAVAILABLE and Microsoft suggests handling it gracefully or retrying. [Obtaining UIA elements](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-obtainingelements), [Element properties](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-automation-element-propids), [GetFocusedElement](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomation-getfocusedelement).

## Win+H and TSF: evidence boundary

Microsoft documents Win+H voice typing as requiring a cursor in a text box and using online recognition powered by Azure Speech. This user documentation does **not** specify its editability detection algorithm or provide an equivalent public detector. Win+H working is useful behavioral evidence, not proof of a particular API implementation. [Voice typing](https://support.microsoft.com/en-us/accessibility/windows/use-voice-typing-to-talk-instead-of-type-on-your-pc).

Microsoft's 2007 article explicitly says Windows Vista **Windows Speech Recognition** uses Text Services Framework (TSF) for insertion, selection, and correction. It also documents a separate fallback for controls without full TSF support. That establishes historical WSR architecture, not modern Win+H internals. [Microsoft's WSR/TSF article](https://learn.microsoft.com/en-us/archive/msdn-magazine/2007/july/speak-up-support-dictation-with-text-services-framework).

TSF exposes document managers and editing contexts to applications/text services. Applications create a thread manager; text services receive one through activation. TF_GetThreadMgr returns a manager previously created in the **calling thread**, or NULL. Thus calling it from ParrotInk does not retrieve Excel's focused text store. A TSF input service would be a separate architectural project, not a drop-in replacement for an external UIA check. The last sentence is an implementation inference from the documented lifecycle. [Thread manager](https://learn.microsoft.com/en-us/windows/win32/tsf/thread-manager), [TF_GetThreadMgr](https://learn.microsoft.com/en-us/windows/win32/api/msctf/nf-msctf-tf_getthreadmgr).

## Local observations and smallest supported correction

The following are supplied live diagnostic observations from this session, not claims that Microsoft guarantees these Excel class names:

| Scenario | Observed target | Consequence |
|---|---|---|
| Selected Excel cell | DataItem 50029, IsReadOnly false | Recognize writable DataItem using its capability; do not require Edit. |
| Copilot prompt | Focus API reports Pane 50033, WebView2Holder/Chrome_WidgetWin_0; its focused descendant is ComboBox 50003, IsReadOnly false | Search the current host's descendants for HasKeyboardFocus true, then apply existing editability checks. |
| In-cell editing | Native EXCEL6 Pane has no descendants; nearest XLDESK parent contains focused Edit 50004, IsReadOnly false | Permit a narrowly bounded fallback to this observed parent container. |
| Whole Excel window search | XLMAIN search finds stale Copilot ComboBox while cell editing | Do not resolve focus by finding an arbitrary focused/editable control across the entire window. |

Recommendation: keep UIA and the existing safety checks, add the missing writable DataItem case, and resolve focused descendants only within the current host or the observed immediate Excel editing container. Test protected/read-only/disabled controls and stale focus before broadening. Do not accept every Pane, every focusable element, or every TextPattern, and do not move focus or press F2 merely to pass detection. Selected-cell insertion can replace a cell's value; preserve the app's existing explicit-dictation behavior and avoid adding any automatic edit-mode transition.

Not established: a public Win+H-compatible detection API, provider guarantees for these Excel classes, or a universal way to infer arbitrary custom-control editability from UIA metadata alone.
