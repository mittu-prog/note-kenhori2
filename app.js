/* note_kenhori2 Read-State Sync & Decryption Engine */
(function() {
    const MASTER_SALT = "note_kenhori2_salt_v1";
    const KEY_VERIFIER = "d52f9c817eebef41";
    const ENC_SYNC_CFG = "Ug68VUUMatoGw2Pn0MQQz82sCiFG3WjVEMtAIQ6Noku6ojr65q+65XCA56PEe2yEPFHggo4I5jrA26PCXBJVTtykpAlNB9514Y8CK8vz04FcrLB9YJ68stzUlFVsC2kpWo3aAyrmmNXYUIQco7Ug";
    const PAGES_URL = "https://mittu-prog.github.io/note-kenhori2/";
    const QR_SVG_DEFAULT = "<svg width=\"29.6mm\" height=\"29.6mm\" version=\"1.1\" viewBox=\"0 0 29.6 29.6\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M1.6,1.6H2.4V2.4H1.6zM2.4,1.6H3.2V2.4H2.4zM3.2,1.6H4V2.4H3.2zM4,1.6H4.8V2.4H4zM4.8,1.6H5.6V2.4H4.8zM5.6,1.6H6.4V2.4H5.6zM6.4,1.6H7.2V2.4H6.4zM8.8,1.6H9.6V2.4H8.8zM9.6,1.6H10.4V2.4H9.6zM10.4,1.6H11.2V2.4H10.4zM11.2,1.6H12V2.4H11.2zM14.4,1.6H15.2V2.4H14.4zM16.8,1.6H17.6V2.4H16.8zM17.6,1.6H18.4V2.4H17.6zM18.4,1.6H19.2V2.4H18.4zM20,1.6H20.8V2.4H20zM20.8,1.6H21.6V2.4H20.8zM22.4,1.6H23.2V2.4H22.4zM23.2,1.6H24V2.4H23.2zM24,1.6H24.8V2.4H24zM24.8,1.6H25.6V2.4H24.8zM25.6,1.6H26.4V2.4H25.6zM26.4,1.6H27.2V2.4H26.4zM27.2,1.6H28V2.4H27.2zM1.6,2.4H2.4V3.2H1.6zM6.4,2.4H7.2V3.2H6.4zM11.2,2.4H12V3.2H11.2zM13.6,2.4H14.4V3.2H13.6zM14.4,2.4H15.2V3.2H14.4zM15.2,2.4H16V3.2H15.2zM16,2.4H16.8V3.2H16zM17.6,2.4H18.4V3.2H17.6zM18.4,2.4H19.2V3.2H18.4zM22.4,2.4H23.2V3.2H22.4zM27.2,2.4H28V3.2H27.2zM1.6,3.2H2.4V4H1.6zM3.2,3.2H4V4H3.2zM4,3.2H4.8V4H4zM4.8,3.2H5.6V4H4.8zM6.4,3.2H7.2V4H6.4zM8,3.2H8.8V4H8zM8.8,3.2H9.6V4H8.8zM11.2,3.2H12V4H11.2zM12.8,3.2H13.6V4H12.8zM14.4,3.2H15.2V4H14.4zM16,3.2H16.8V4H16zM18.4,3.2H19.2V4H18.4zM22.4,3.2H23.2V4H22.4zM24,3.2H24.8V4H24zM24.8,3.2H25.6V4H24.8zM25.6,3.2H26.4V4H25.6zM27.2,3.2H28V4H27.2zM1.6,4H2.4V4.8H1.6zM3.2,4H4V4.8H3.2zM4,4H4.8V4.8H4zM4.8,4H5.6V4.8H4.8zM6.4,4H7.2V4.8H6.4zM8,4H8.8V4.8H8zM8.8,4H9.6V4.8H8.8zM10.4,4H11.2V4.8H10.4zM15.2,4H16V4.8H15.2zM16.8,4H17.6V4.8H16.8zM17.6,4H18.4V4.8H17.6zM19.2,4H20V4.8H19.2zM22.4,4H23.2V4.8H22.4zM24,4H24.8V4.8H24zM24.8,4H25.6V4.8H24.8zM25.6,4H26.4V4.8H25.6zM27.2,4H28V4.8H27.2zM1.6,4.8H2.4V5.6H1.6zM3.2,4.8H4V5.6H3.2zM4,4.8H4.8V5.6H4zM4.8,4.8H5.6V5.6H4.8zM6.4,4.8H7.2V5.6H6.4zM8,4.8H8.8V5.6H8zM8.8,4.8H9.6V5.6H8.8zM10.4,4.8H11.2V5.6H10.4zM11.2,4.8H12V5.6H11.2zM12,4.8H12.8V5.6H12zM12.8,4.8H13.6V5.6H12.8zM13.6,4.8H14.4V5.6H13.6zM14.4,4.8H15.2V5.6H14.4zM16,4.8H16.8V5.6H16zM16.8,4.8H17.6V5.6H16.8zM17.6,4.8H18.4V5.6H17.6zM19.2,4.8H20V5.6H19.2zM20,4.8H20.8V5.6H20zM22.4,4.8H23.2V5.6H22.4zM24,4.8H24.8V5.6H24zM24.8,4.8H25.6V5.6H24.8zM25.6,4.8H26.4V5.6H25.6zM27.2,4.8H28V5.6H27.2zM1.6,5.6H2.4V6.4H1.6zM6.4,5.6H7.2V6.4H6.4zM8,5.6H8.8V6.4H8zM8.8,5.6H9.6V6.4H8.8zM10.4,5.6H11.2V6.4H10.4zM12,5.6H12.8V6.4H12zM12.8,5.6H13.6V6.4H12.8zM17.6,5.6H18.4V6.4H17.6zM18.4,5.6H19.2V6.4H18.4zM19.2,5.6H20V6.4H19.2zM22.4,5.6H23.2V6.4H22.4zM27.2,5.6H28V6.4H27.2zM1.6,6.4H2.4V7.2H1.6zM2.4,6.4H3.2V7.2H2.4zM3.2,6.4H4V7.2H3.2zM4,6.4H4.8V7.2H4zM4.8,6.4H5.6V7.2H4.8zM5.6,6.4H6.4V7.2H5.6zM6.4,6.4H7.2V7.2H6.4zM8,6.4H8.8V7.2H8zM9.6,6.4H10.4V7.2H9.6zM11.2,6.4H12V7.2H11.2zM12.8,6.4H13.6V7.2H12.8zM14.4,6.4H15.2V7.2H14.4zM16,6.4H16.8V7.2H16zM17.6,6.4H18.4V7.2H17.6zM19.2,6.4H20V7.2H19.2zM20.8,6.4H21.6V7.2H20.8zM22.4,6.4H23.2V7.2H22.4zM23.2,6.4H24V7.2H23.2zM24,6.4H24.8V7.2H24zM24.8,6.4H25.6V7.2H24.8zM25.6,6.4H26.4V7.2H25.6zM26.4,6.4H27.2V7.2H26.4zM27.2,6.4H28V7.2H27.2zM8,7.2H8.8V8H8zM8.8,7.2H9.6V8H8.8zM9.6,7.2H10.4V8H9.6zM14.4,7.2H15.2V8H14.4zM16,7.2H16.8V8H16zM16.8,7.2H17.6V8H16.8zM17.6,7.2H18.4V8H17.6zM18.4,7.2H19.2V8H18.4zM19.2,7.2H20V8H19.2zM20,7.2H20.8V8H20zM20.8,7.2H21.6V8H20.8zM1.6,8H2.4V8.8H1.6zM3.2,8H4V8.8H3.2zM4,8H4.8V8.8H4zM4.8,8H5.6V8.8H4.8zM5.6,8H6.4V8.8H5.6zM6.4,8H7.2V8.8H6.4zM10.4,8H11.2V8.8H10.4zM12,8H12.8V8.8H12zM12.8,8H13.6V8.8H12.8zM15.2,8H16V8.8H15.2zM16.8,8H17.6V8.8H16.8zM19.2,8H20V8.8H19.2zM22.4,8H23.2V8.8H22.4zM23.2,8H24V8.8H23.2zM24,8H24.8V8.8H24zM24.8,8H25.6V8.8H24.8zM25.6,8H26.4V8.8H25.6zM2.4,8.8H3.2V9.6H2.4zM3.2,8.8H4V9.6H3.2zM4,8.8H4.8V9.6H4zM4.8,8.8H5.6V9.6H4.8zM8,8.8H8.8V9.6H8zM8.8,8.8H9.6V9.6H8.8zM9.6,8.8H10.4V9.6H9.6zM11.2,8.8H12V9.6H11.2zM12,8.8H12.8V9.6H12zM15.2,8.8H16V9.6H15.2zM16,8.8H16.8V9.6H16zM16.8,8.8H17.6V9.6H16.8zM17.6,8.8H18.4V9.6H17.6zM18.4,8.8H19.2V9.6H18.4zM19.2,8.8H20V9.6H19.2zM20,8.8H20.8V9.6H20zM22.4,8.8H23.2V9.6H22.4zM23.2,8.8H24V9.6H23.2zM24.8,8.8H25.6V9.6H24.8zM25.6,8.8H26.4V9.6H25.6zM27.2,8.8H28V9.6H27.2zM3.2,9.6H4V10.4H3.2zM4,9.6H4.8V10.4H4zM5.6,9.6H6.4V10.4H5.6zM6.4,9.6H7.2V10.4H6.4zM8,9.6H8.8V10.4H8zM9.6,9.6H10.4V10.4H9.6zM12,9.6H12.8V10.4H12zM12.8,9.6H13.6V10.4H12.8zM13.6,9.6H14.4V10.4H13.6zM14.4,9.6H15.2V10.4H14.4zM16,9.6H16.8V10.4H16zM17.6,9.6H18.4V10.4H17.6zM19.2,9.6H20V10.4H19.2zM20.8,9.6H21.6V10.4H20.8zM21.6,9.6H22.4V10.4H21.6zM22.4,9.6H23.2V10.4H22.4zM24,9.6H24.8V10.4H24zM25.6,9.6H26.4V10.4H25.6zM3.2,10.4H4V11.2H3.2zM4,10.4H4.8V11.2H4zM4.8,10.4H5.6V11.2H4.8zM8,10.4H8.8V11.2H8zM8.8,10.4H9.6V11.2H8.8zM10.4,10.4H11.2V11.2H10.4zM11.2,10.4H12V11.2H11.2zM12,10.4H12.8V11.2H12zM14.4,10.4H15.2V11.2H14.4zM16.8,10.4H17.6V11.2H16.8zM17.6,10.4H18.4V11.2H17.6zM18.4,10.4H19.2V11.2H18.4zM19.2,10.4H20V11.2H19.2zM21.6,10.4H22.4V11.2H21.6zM22.4,10.4H23.2V11.2H22.4zM24,10.4H24.8V11.2H24zM24.8,10.4H25.6V11.2H24.8zM25.6,10.4H26.4V11.2H25.6zM26.4,10.4H27.2V11.2H26.4zM1.6,11.2H2.4V12H1.6zM4,11.2H4.8V12H4zM5.6,11.2H6.4V12H5.6zM6.4,11.2H7.2V12H6.4zM7.2,11.2H8V12H7.2zM9.6,11.2H10.4V12H9.6zM10.4,11.2H11.2V12H10.4zM11.2,11.2H12V12H11.2zM12.8,11.2H13.6V12H12.8zM14.4,11.2H15.2V12H14.4zM15.2,11.2H16V12H15.2zM16,11.2H16.8V12H16zM20.8,11.2H21.6V12H20.8zM21.6,11.2H22.4V12H21.6zM23.2,11.2H24V12H23.2zM24,11.2H24.8V12H24zM24.8,11.2H25.6V12H24.8zM26.4,11.2H27.2V12H26.4zM1.6,12H2.4V12.8H1.6zM2.4,12H3.2V12.8H2.4zM4.8,12H5.6V12.8H4.8zM5.6,12H6.4V12.8H5.6zM7.2,12H8V12.8H7.2zM8,12H8.8V12.8H8zM8.8,12H9.6V12.8H8.8zM9.6,12H10.4V12.8H9.6zM10.4,12H11.2V12.8H10.4zM13.6,12H14.4V12.8H13.6zM15.2,12H16V12.8H15.2zM16.8,12H17.6V12.8H16.8zM17.6,12H18.4V12.8H17.6zM18.4,12H19.2V12.8H18.4zM19.2,12H20V12.8H19.2zM20,12H20.8V12.8H20zM20.8,12H21.6V12.8H20.8zM21.6,12H22.4V12.8H21.6zM22.4,12H23.2V12.8H22.4zM24.8,12H25.6V12.8H24.8zM26.4,12H27.2V12.8H26.4zM27.2,12H28V12.8H27.2zM1.6,12.8H2.4V13.6H1.6zM3.2,12.8H4V13.6H3.2zM4.8,12.8H5.6V13.6H4.8zM6.4,12.8H7.2V13.6H6.4zM8.8,12.8H9.6V13.6H8.8zM9.6,12.8H10.4V13.6H9.6zM13.6,12.8H14.4V13.6H13.6zM14.4,12.8H15.2V13.6H14.4zM16,12.8H16.8V13.6H16zM18.4,12.8H19.2V13.6H18.4zM21.6,12.8H22.4V13.6H21.6zM22.4,12.8H23.2V13.6H22.4zM23.2,12.8H24V13.6H23.2zM24.8,12.8H25.6V13.6H24.8zM25.6,12.8H26.4V13.6H25.6zM26.4,12.8H27.2V13.6H26.4zM2.4,13.6H3.2V14.4H2.4zM4.8,13.6H5.6V14.4H4.8zM5.6,13.6H6.4V14.4H5.6zM7.2,13.6H8V14.4H7.2zM8,13.6H8.8V14.4H8zM8.8,13.6H9.6V14.4H8.8zM9.6,13.6H10.4V14.4H9.6zM10.4,13.6H11.2V14.4H10.4zM12.8,13.6H13.6V14.4H12.8zM13.6,13.6H14.4V14.4H13.6zM16,13.6H16.8V14.4H16zM18.4,13.6H19.2V14.4H18.4zM20,13.6H20.8V14.4H20zM21.6,13.6H22.4V14.4H21.6zM22.4,13.6H23.2V14.4H22.4zM23.2,13.6H24V14.4H23.2zM24,13.6H24.8V14.4H24zM24.8,13.6H25.6V14.4H24.8zM25.6,13.6H26.4V14.4H25.6zM1.6,14.4H2.4V15.2H1.6zM3.2,14.4H4V15.2H3.2zM4.8,14.4H5.6V15.2H4.8zM5.6,14.4H6.4V15.2H5.6zM6.4,14.4H7.2V15.2H6.4zM8.8,14.4H9.6V15.2H8.8zM10.4,14.4H11.2V15.2H10.4zM12.8,14.4H13.6V15.2H12.8zM13.6,14.4H14.4V15.2H13.6zM15.2,14.4H16V15.2H15.2zM16.8,14.4H17.6V15.2H16.8zM19.2,14.4H20V15.2H19.2zM20,14.4H20.8V15.2H20zM21.6,14.4H22.4V15.2H21.6zM23.2,14.4H24V15.2H23.2zM24,14.4H24.8V15.2H24zM27.2,14.4H28V15.2H27.2zM3.2,15.2H4V16H3.2zM4,15.2H4.8V16H4zM4.8,15.2H5.6V16H4.8zM7.2,15.2H8V16H7.2zM9.6,15.2H10.4V16H9.6zM10.4,15.2H11.2V16H10.4zM11.2,15.2H12V16H11.2zM12,15.2H12.8V16H12zM14.4,15.2H15.2V16H14.4zM16.8,15.2H17.6V16H16.8zM17.6,15.2H18.4V16H17.6zM19.2,15.2H20V16H19.2zM20,15.2H20.8V16H20zM22.4,15.2H23.2V16H22.4zM23.2,15.2H24V16H23.2zM24.8,15.2H25.6V16H24.8zM25.6,15.2H26.4V16H25.6zM27.2,15.2H28V16H27.2zM1.6,16H2.4V16.8H1.6zM2.4,16H3.2V16.8H2.4zM6.4,16H7.2V16.8H6.4zM8,16H8.8V16.8H8zM8.8,16H9.6V16.8H8.8zM9.6,16H10.4V16.8H9.6zM10.4,16H11.2V16.8H10.4zM12,16H12.8V16.8H12zM13.6,16H14.4V16.8H13.6zM14.4,16H15.2V16.8H14.4zM15.2,16H16V16.8H15.2zM16,16H16.8V16.8H16zM18.4,16H19.2V16.8H18.4zM19.2,16H20V16.8H19.2zM20.8,16H21.6V16.8H20.8zM23.2,16H24V16.8H23.2zM24,16H24.8V16.8H24zM25.6,16H26.4V16.8H25.6zM26.4,16H27.2V16.8H26.4zM2.4,16.8H3.2V17.6H2.4zM3.2,16.8H4V17.6H3.2zM4,16.8H4.8V17.6H4zM7.2,16.8H8V17.6H7.2zM11.2,16.8H12V17.6H11.2zM12.8,16.8H13.6V17.6H12.8zM13.6,16.8H14.4V17.6H13.6zM16,16.8H16.8V17.6H16zM16.8,16.8H17.6V17.6H16.8zM17.6,16.8H18.4V17.6H17.6zM18.4,16.8H19.2V17.6H18.4zM19.2,16.8H20V17.6H19.2zM22.4,16.8H23.2V17.6H22.4zM23.2,16.8H24V17.6H23.2zM24,16.8H24.8V17.6H24zM24.8,16.8H25.6V17.6H24.8zM25.6,16.8H26.4V17.6H25.6zM2.4,17.6H3.2V18.4H2.4zM3.2,17.6H4V18.4H3.2zM4,17.6H4.8V18.4H4zM6.4,17.6H7.2V18.4H6.4zM7.2,17.6H8V18.4H7.2zM8,17.6H8.8V18.4H8zM11.2,17.6H12V18.4H11.2zM16,17.6H16.8V18.4H16zM16.8,17.6H17.6V18.4H16.8zM19.2,17.6H20V18.4H19.2zM20.8,17.6H21.6V18.4H20.8zM21.6,17.6H22.4V18.4H21.6zM23.2,17.6H24V18.4H23.2zM24,17.6H24.8V18.4H24zM24.8,17.6H25.6V18.4H24.8zM26.4,17.6H27.2V18.4H26.4zM1.6,18.4H2.4V19.2H1.6zM4.8,18.4H5.6V19.2H4.8zM5.6,18.4H6.4V19.2H5.6zM10.4,18.4H11.2V19.2H10.4zM13.6,18.4H14.4V19.2H13.6zM14.4,18.4H15.2V19.2H14.4zM16,18.4H16.8V19.2H16zM16.8,18.4H17.6V19.2H16.8zM17.6,18.4H18.4V19.2H17.6zM18.4,18.4H19.2V19.2H18.4zM20,18.4H20.8V19.2H20zM20.8,18.4H21.6V19.2H20.8zM22.4,18.4H23.2V19.2H22.4zM27.2,18.4H28V19.2H27.2zM1.6,19.2H2.4V20H1.6zM3.2,19.2H4V20H3.2zM4,19.2H4.8V20H4zM6.4,19.2H7.2V20H6.4zM8.8,19.2H9.6V20H8.8zM9.6,19.2H10.4V20H9.6zM11.2,19.2H12V20H11.2zM12,19.2H12.8V20H12zM20.8,19.2H21.6V20H20.8zM21.6,19.2H22.4V20H21.6zM22.4,19.2H23.2V20H22.4zM23.2,19.2H24V20H23.2zM24,19.2H24.8V20H24zM24.8,19.2H25.6V20H24.8zM26.4,19.2H27.2V20H26.4zM1.6,20H2.4V20.8H1.6zM4.8,20H5.6V20.8H4.8zM11.2,20H12V20.8H11.2zM12,20H12.8V20.8H12zM14.4,20H15.2V20.8H14.4zM16.8,20H17.6V20.8H16.8zM17.6,20H18.4V20.8H17.6zM18.4,20H19.2V20.8H18.4zM20,20H20.8V20.8H20zM20.8,20H21.6V20.8H20.8zM21.6,20H22.4V20.8H21.6zM24,20H24.8V20.8H24zM24.8,20H25.6V20.8H24.8zM25.6,20H26.4V20.8H25.6zM26.4,20H27.2V20.8H26.4zM27.2,20H28V20.8H27.2zM1.6,20.8H2.4V21.6H1.6zM3.2,20.8H4V21.6H3.2zM4,20.8H4.8V21.6H4zM4.8,20.8H5.6V21.6H4.8zM5.6,20.8H6.4V21.6H5.6zM6.4,20.8H7.2V21.6H6.4zM8.8,20.8H9.6V21.6H8.8zM9.6,20.8H10.4V21.6H9.6zM10.4,20.8H11.2V21.6H10.4zM12,20.8H12.8V21.6H12zM15.2,20.8H16V21.6H15.2zM16.8,20.8H17.6V21.6H16.8zM19.2,20.8H20V21.6H19.2zM20.8,20.8H21.6V21.6H20.8zM21.6,20.8H22.4V21.6H21.6zM22.4,20.8H23.2V21.6H22.4zM23.2,20.8H24V21.6H23.2zM24,20.8H24.8V21.6H24zM26.4,20.8H27.2V21.6H26.4zM8,21.6H8.8V22.4H8zM8.8,21.6H9.6V22.4H8.8zM10.4,21.6H11.2V22.4H10.4zM12.8,21.6H13.6V22.4H12.8zM14.4,21.6H15.2V22.4H14.4zM15.2,21.6H16V22.4H15.2zM16,21.6H16.8V22.4H16zM16.8,21.6H17.6V22.4H16.8zM20,21.6H20.8V22.4H20zM20.8,21.6H21.6V22.4H20.8zM24,21.6H24.8V22.4H24zM25.6,21.6H26.4V22.4H25.6zM26.4,21.6H27.2V22.4H26.4zM27.2,21.6H28V22.4H27.2zM1.6,22.4H2.4V23.2H1.6zM2.4,22.4H3.2V23.2H2.4zM3.2,22.4H4V23.2H3.2zM4,22.4H4.8V23.2H4zM4.8,22.4H5.6V23.2H4.8zM5.6,22.4H6.4V23.2H5.6zM6.4,22.4H7.2V23.2H6.4zM8.8,22.4H9.6V23.2H8.8zM10.4,22.4H11.2V23.2H10.4zM12.8,22.4H13.6V23.2H12.8zM13.6,22.4H14.4V23.2H13.6zM15.2,22.4H16V23.2H15.2zM17.6,22.4H18.4V23.2H17.6zM20,22.4H20.8V23.2H20zM20.8,22.4H21.6V23.2H20.8zM22.4,22.4H23.2V23.2H22.4zM24,22.4H24.8V23.2H24zM25.6,22.4H26.4V23.2H25.6zM26.4,22.4H27.2V23.2H26.4zM1.6,23.2H2.4V24H1.6zM6.4,23.2H7.2V24H6.4zM8,23.2H8.8V24H8zM8.8,23.2H9.6V24H8.8zM10.4,23.2H11.2V24H10.4zM11.2,23.2H12V24H11.2zM12.8,23.2H13.6V24H12.8zM14.4,23.2H15.2V24H14.4zM15.2,23.2H16V24H15.2zM16,23.2H16.8V24H16zM16.8,23.2H17.6V24H16.8zM17.6,23.2H18.4V24H17.6zM18.4,23.2H19.2V24H18.4zM19.2,23.2H20V24H19.2zM20,23.2H20.8V24H20zM20.8,23.2H21.6V24H20.8zM24,23.2H24.8V24H24zM24.8,23.2H25.6V24H24.8zM25.6,23.2H26.4V24H25.6zM26.4,23.2H27.2V24H26.4zM27.2,23.2H28V24H27.2zM1.6,24H2.4V24.8H1.6zM3.2,24H4V24.8H3.2zM4,24H4.8V24.8H4zM4.8,24H5.6V24.8H4.8zM6.4,24H7.2V24.8H6.4zM8,24H8.8V24.8H8zM8.8,24H9.6V24.8H8.8zM9.6,24H10.4V24.8H9.6zM10.4,24H11.2V24.8H10.4zM11.2,24H12V24.8H11.2zM14.4,24H15.2V24.8H14.4zM19.2,24H20V24.8H19.2zM20.8,24H21.6V24.8H20.8zM21.6,24H22.4V24.8H21.6zM22.4,24H23.2V24.8H22.4zM23.2,24H24V24.8H23.2zM24,24H24.8V24.8H24zM24.8,24H25.6V24.8H24.8zM26.4,24H27.2V24.8H26.4zM27.2,24H28V24.8H27.2zM1.6,24.8H2.4V25.6H1.6zM3.2,24.8H4V25.6H3.2zM4,24.8H4.8V25.6H4zM4.8,24.8H5.6V25.6H4.8zM6.4,24.8H7.2V25.6H6.4zM8,24.8H8.8V25.6H8zM10.4,24.8H11.2V25.6H10.4zM12.8,24.8H13.6V25.6H12.8zM13.6,24.8H14.4V25.6H13.6zM16,24.8H16.8V25.6H16zM16.8,24.8H17.6V25.6H16.8zM17.6,24.8H18.4V25.6H17.6zM20,24.8H20.8V25.6H20zM20.8,24.8H21.6V25.6H20.8zM21.6,24.8H22.4V25.6H21.6zM24,24.8H24.8V25.6H24zM24.8,24.8H25.6V25.6H24.8zM25.6,24.8H26.4V25.6H25.6zM26.4,24.8H27.2V25.6H26.4zM27.2,24.8H28V25.6H27.2zM1.6,25.6H2.4V26.4H1.6zM3.2,25.6H4V26.4H3.2zM4,25.6H4.8V26.4H4zM4.8,25.6H5.6V26.4H4.8zM6.4,25.6H7.2V26.4H6.4zM8,25.6H8.8V26.4H8zM8.8,25.6H9.6V26.4H8.8zM10.4,25.6H11.2V26.4H10.4zM11.2,25.6H12V26.4H11.2zM13.6,25.6H14.4V26.4H13.6zM14.4,25.6H15.2V26.4H14.4zM15.2,25.6H16V26.4H15.2zM16,25.6H16.8V26.4H16zM17.6,25.6H18.4V26.4H17.6zM19.2,25.6H20V26.4H19.2zM22.4,25.6H23.2V26.4H22.4zM23.2,25.6H24V26.4H23.2zM24.8,25.6H25.6V26.4H24.8zM25.6,25.6H26.4V26.4H25.6zM1.6,26.4H2.4V27.2H1.6zM6.4,26.4H7.2V27.2H6.4zM12,26.4H12.8V27.2H12zM12.8,26.4H13.6V27.2H12.8zM13.6,26.4H14.4V27.2H13.6zM16,26.4H16.8V27.2H16zM17.6,26.4H18.4V27.2H17.6zM18.4,26.4H19.2V27.2H18.4zM19.2,26.4H20V27.2H19.2zM20,26.4H20.8V27.2H20zM22.4,26.4H23.2V27.2H22.4zM24,26.4H24.8V27.2H24zM24.8,26.4H25.6V27.2H24.8zM25.6,26.4H26.4V27.2H25.6zM1.6,27.2H2.4V28H1.6zM2.4,27.2H3.2V28H2.4zM3.2,27.2H4V28H3.2zM4,27.2H4.8V28H4zM4.8,27.2H5.6V28H4.8zM5.6,27.2H6.4V28H5.6zM6.4,27.2H7.2V28H6.4zM8,27.2H8.8V28H8zM9.6,27.2H10.4V28H9.6zM10.4,27.2H11.2V28H10.4zM11.2,27.2H12V28H11.2zM12,27.2H12.8V28H12zM12.8,27.2H13.6V28H12.8zM13.6,27.2H14.4V28H13.6zM15.2,27.2H16V28H15.2zM16,27.2H16.8V28H16zM19.2,27.2H20V28H19.2zM20.8,27.2H21.6V28H20.8zM21.6,27.2H22.4V28H21.6zM23.2,27.2H24V28H23.2zM26.4,27.2H27.2V28H26.4z\" id=\"qr-path\" fill=\"#000000\" fill-opacity=\"1\" fill-rule=\"nonzero\" stroke=\"none\" /></svg>";
    const STORAGE_KEY_READ = "note_kenhori2_read_v1";
    const STORAGE_KEY_MK = "note_kenhori2_mk_v1";
    const STORAGE_KEY_PW = "note_kenhori2_pw_v1";

    // --- Pure-JS SHA-256 (works on both file:// and https://) ---
    const K256 = new Uint32Array([
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
    ]);

    function rotr(n, x) { return (x >>> n) | (x << (32 - n)); }

    function sha256Bytes(msgBytes) {
        const l = msgBytes.length;
        const bitLenHi = Math.floor((l * 8) / 0x100000000);
        const bitLenLo = (l * 8) >>> 0;
        const padLen = ((l + 9 + 63) & ~63);
        const buf = new Uint8Array(padLen);
        buf.set(msgBytes);
        buf[l] = 0x80;
        const dv = new DataView(buf.buffer);
        dv.setUint32(padLen - 8, bitLenHi, false);
        dv.setUint32(padLen - 4, bitLenLo, false);

        let H0 = 0x6a09e667, H1 = 0xbb67ae85, H2 = 0x3c6ef372, H3 = 0xa54ff53a;
        let H4 = 0x510e527f, H5 = 0x9b05688c, H6 = 0x1f83d9ab, H7 = 0x5be0cd19;
        const W = new Uint32Array(64);

        for (let offset = 0; offset < padLen; offset += 64) {
            for (let i = 0; i < 16; i++) {
                W[i] = dv.getUint32(offset + i * 4, false);
            }
            for (let i = 16; i < 64; i++) {
                const s0 = rotr(7, W[i - 15]) ^ rotr(18, W[i - 15]) ^ (W[i - 15] >>> 3);
                const s1 = rotr(17, W[i - 2]) ^ rotr(19, W[i - 2]) ^ (W[i - 2] >>> 10);
                W[i] = (W[i - 16] + s0 + W[i - 7] + s1) >>> 0;
            }
            let a = H0, b = H1, c = H2, d = H3, e = H4, f = H5, g = H6, h = H7;
            for (let i = 0; i < 64; i++) {
                const S1 = rotr(6, e) ^ rotr(11, e) ^ rotr(25, e);
                const ch = (e & f) ^ (~e & g);
                const temp1 = (h + S1 + ch + K256[i] + W[i]) >>> 0;
                const S0 = rotr(2, a) ^ rotr(13, a) ^ rotr(22, a);
                const maj = (a & b) ^ (a & c) ^ (b & c);
                const temp2 = (S0 + maj) >>> 0;
                h = g; g = f; f = e; e = (d + temp1) >>> 0;
                d = c; c = b; b = a; a = (temp1 + temp2) >>> 0;
            }
            H0 = (H0 + a) >>> 0; H1 = (H1 + b) >>> 0; H2 = (H2 + c) >>> 0; H3 = (H3 + d) >>> 0;
            H4 = (H4 + e) >>> 0; H5 = (H5 + f) >>> 0; H6 = (H6 + g) >>> 0; H7 = (H7 + h) >>> 0;
        }
        const out = new Uint8Array(32);
        const outDv = new DataView(out.buffer);
        outDv.setUint32(0, H0, false); outDv.setUint32(4, H1, false);
        outDv.setUint32(8, H2, false); outDv.setUint32(12, H3, false);
        outDv.setUint32(16, H4, false); outDv.setUint32(20, H5, false);
        outDv.setUint32(24, H6, false); outDv.setUint32(28, H7, false);
        return out;
    }

    function bytesToHex(bytes) {
        let s = "";
        for (let i = 0; i < bytes.length; i++) {
            s += bytes[i].toString(16).padStart(2, "0");
        }
        return s;
    }

    function hexToBytes(hex) {
        const out = new Uint8Array(hex.length / 2);
        for (let i = 0; i < out.length; i++) {
            out[i] = parseInt(hex.substr(i * 2, 2), 16);
        }
        return out;
    }

    function deriveKey32(password) {
        const enc = new TextEncoder();
        const data = enc.encode(MASTER_SALT + ":" + password);
        let h = sha256Bytes(data);
        const combined = new Uint8Array(32 + data.length);
        combined.set(data, 32);
        for (let i = 0; i < 1000; i++) {
            combined.set(h, 0);
            h = sha256Bytes(combined);
        }
        return h;
    }

    function verifyKey32(key32) {
        if (!key32 || key32.length !== 32) return false;
        const suffix = new TextEncoder().encode(":verify_v1");
        const buf = new Uint8Array(32 + suffix.length);
        buf.set(key32, 0);
        buf.set(suffix, 32);
        const vHex = bytesToHex(sha256Bytes(buf)).slice(0, 16);
        return vHex === KEY_VERIFIER;
    }

    function rotl32(v, c) { return ((v << c) | (v >>> (32 - c))) >>> 0; }

    function qround(x, a, b, c, d) {
        x[a] = (x[a] + x[b]) >>> 0; x[d] = rotl32(x[d] ^ x[a], 16);
        x[c] = (x[c] + x[d]) >>> 0; x[b] = rotl32(x[b] ^ x[c], 12);
        x[a] = (x[a] + x[b]) >>> 0; x[d] = rotl32(x[d] ^ x[a], 8);
        x[c] = (x[c] + x[d]) >>> 0; x[b] = rotl32(x[b] ^ x[c], 7);
    }

    function chacha20Xor(key32, nonce12, dataBytes) {
        const keyDv = new DataView(key32.buffer, key32.byteOffset, 32);
        const nonceDv = new DataView(nonce12.buffer, nonce12.byteOffset, 12);
        const state = new Uint32Array(16);
        state[0] = 0x61707865; state[1] = 0x3320646e;
        state[2] = 0x79622d32; state[3] = 0x6b206574;
        for (let i = 0; i < 8; i++) state[4 + i] = keyDv.getUint32(i * 4, true);
        for (let i = 0; i < 3; i++) state[13 + i] = nonceDv.getUint32(i * 4, true);

        const out = new Uint8Array(dataBytes.length);
        const working = new Uint32Array(16);
        const ksBytes = new Uint8Array(64);
        const ksDv = new DataView(ksBytes.buffer);
        const blocks = Math.ceil(dataBytes.length / 64);

        for (let b = 0; b < blocks; b++) {
            state[12] = b >>> 0;
            working.set(state);
            for (let r = 0; r < 10; r++) {
                qround(working, 0, 4, 8, 12); qround(working, 1, 5, 9, 13);
                qround(working, 2, 6, 10, 14); qround(working, 3, 7, 11, 15);
                qround(working, 0, 5, 10, 15); qround(working, 1, 6, 11, 12);
                qround(working, 2, 7, 8, 13); qround(working, 3, 4, 9, 14);
            }
            for (let i = 0; i < 16; i++) {
                ksDv.setUint32(i * 4, (working[i] + state[i]) >>> 0, true);
            }
            const offset = b * 64;
            const limit = Math.min(64, dataBytes.length - offset);
            for (let i = 0; i < limit; i++) {
                out[offset + i] = dataBytes[offset + i] ^ ksBytes[i];
            }
        }
        return out;
    }

    function decryptBase64(b64, key32) {
        const binStr = atob(b64);
        const raw = new Uint8Array(binStr.length);
        for (let i = 0; i < binStr.length; i++) raw[i] = binStr.charCodeAt(i);
        const nonce12 = raw.subarray(0, 12);
        const ct = raw.subarray(12);
        const ptBytes = chacha20Xor(key32, nonce12, ct);
        return new TextDecoder("utf-8").decode(ptBytes);
    }

    // --- Key / Password Resolution ---
    let activeKey32 = null;
    let activePassword = null;
    let syncConfig = null;

    function loadWindowNameCache() {
        try {
            if (window.name && window.name.startsWith("NOTE_KH2:")) {
                return JSON.parse(window.name.slice(9));
            }
        } catch (e) {}
        return {};
    }

    function saveWindowNameCache(obj) {
        try {
            const cur = loadWindowNameCache();
            Object.assign(cur, obj);
            window.name = "NOTE_KH2:" + JSON.stringify(cur);
        } catch (e) {}
    }

    function tryUnlockWithPassword(pw) {
        if (!pw) return false;
        const k = deriveKey32(pw);
        if (verifyKey32(k)) {
            activeKey32 = k;
            activePassword = pw;
            const mkHex = bytesToHex(k);
            try {
                localStorage.setItem(STORAGE_KEY_MK, mkHex);
                localStorage.setItem(STORAGE_KEY_PW, pw);
            } catch (e) {}
            saveWindowNameCache({ mk: mkHex, pw: pw });
            initSyncConfig();
            return true;
        }
        return false;
    }

    function initSyncConfig() {
        if (!activeKey32 || syncConfig) return;
        try {
            const jsonStr = decryptBase64(ENC_SYNC_CFG, activeKey32);
            syncConfig = JSON.parse(jsonStr);
        } catch (e) {
            console.warn("Failed to decrypt sync config:", e);
        }
    }

    function autoResolveKey() {
        // 1. Check URL hash #pw=...
        if (location.hash && location.hash.includes("pw=")) {
            const m = location.hash.match(/[#&]pw=([^&]+)/);
            if (m && m[1]) {
                const pw = decodeURIComponent(m[1]);
                if (tryUnlockWithPassword(pw)) {
                    try {
                        history.replaceState(null, "", location.pathname + location.search);
                    } catch (e) {}
                    return true;
                }
            }
        }
        // 2. Check cached Master Key in localStorage or window.name
        try {
            const wn = loadWindowNameCache();
            const mkHex = localStorage.getItem(STORAGE_KEY_MK) || wn.mk;
            const savedPw = localStorage.getItem(STORAGE_KEY_PW) || wn.pw;
            if (mkHex && mkHex.length === 64) {
                const k = hexToBytes(mkHex);
                if (verifyKey32(k)) {
                    activeKey32 = k;
                    activePassword = savedPw || "";
                    saveWindowNameCache({ mk: mkHex, pw: activePassword });
                    initSyncConfig();
                    return true;
                }
            }
        } catch (e) {}
        // 3. Check local_key.js (present on local PC, gitignored on GitHub Pages)
        if (window.__NOTE_LOCAL_PASS__) {
            if (tryUnlockWithPassword(window.__NOTE_LOCAL_PASS__)) {
                return true;
            }
        }
        return false;
    }

    // --- Read State CRDT Store (localStorage + window.name + GitHub Gist) ---
    // Format: { [noteKey]: { r: 1 | 0, t: timestamp_ms } }
    let readState = {};
    let syncInProgress = false;
    let syncTimer = null;

    function loadLocalReadState() {
        let merged = {};
        try {
            const wn = loadWindowNameCache();
            if (wn.readState && typeof wn.readState === "object") {
                merged = Object.assign({}, wn.readState);
            }
        } catch (e) {}
        try {
            const raw = localStorage.getItem(STORAGE_KEY_READ);
            if (raw) {
                const parsed = JSON.parse(raw);
                mergeStates(merged, parsed);
            }
        } catch (e) {}
        readState = merged;
    }

    function saveLocalReadState() {
        try {
            localStorage.setItem(STORAGE_KEY_READ, JSON.stringify(readState));
        } catch (e) {}
        saveWindowNameCache({ readState: readState });
    }

    function mergeStates(target, incoming) {
        if (!incoming || typeof incoming !== "object") return false;
        let changed = false;
        for (const [k, val] of Object.entries(incoming)) {
            if (!val || typeof val !== "object") continue;
            const inT = Number(val.t) || 0;
            const inR = val.r ? 1 : 0;
            const cur = target[k];
            if (!cur || inT > (Number(cur.t) || 0)) {
                if (!cur || cur.r !== inR || cur.t !== inT) {
                    target[k] = { r: inR, t: inT };
                    changed = true;
                }
            }
        }
        return changed;
    }

    function isArticleRead(key) {
        return Boolean(readState[key] && readState[key].r === 1);
    }

    function setArticleRead(key, isRead) {
        if (!key) return;
        readState[key] = {
            r: isRead ? 1 : 0,
            t: Date.now()
        };
        saveLocalReadState();
        refreshReadUI();
        scheduleCloudSync(true);
    }

    function toggleArticleRead(key) {
        setArticleRead(key, !isArticleRead(key));
    }

    function updateSyncStatusUI(state, text) {
        const els = document.querySelectorAll(".sync-status");
        els.forEach(el => {
            el.className = "sync-status " + (state || "");
            el.textContent = text;
        });
    }

    function scheduleCloudSync(pushImmediately) {
        if (syncTimer) clearTimeout(syncTimer);
        syncTimer = setTimeout(() => syncWithGist(pushImmediately), pushImmediately ? 350 : 50);
    }

    async function syncWithGist(forcePush) {
        if (!syncConfig || !syncConfig.token || !syncConfig.gistId) {
            updateSyncStatusUI("err", "🔒 パスワード未解除");
            return;
        }
        if (syncInProgress) return;
        syncInProgress = true;
        updateSyncStatusUI("", "🔄 同期中...");

        try {
            const resp = await fetch("https://api.github.com/gists/" + syncConfig.gistId, {
                method: "GET",
                headers: {
                    "Accept": "application/vnd.github+json",
                    "Authorization": "Bearer " + syncConfig.token
                },
                cache: "no-store"
            });
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const gistData = await resp.json();
            const fileObj = gistData.files && gistData.files["note_kenhori2_read_state.json"];
            let remoteItems = {};
            if (fileObj && fileObj.content) {
                try {
                    const parsed = JSON.parse(fileObj.content);
                    remoteItems = parsed.items || {};
                } catch (e) {}
            }

            const localUpdatedFromRemote = mergeStates(readState, remoteItems);
            const remoteNeedsUpdate = forcePush || mergeStates(remoteItems, readState);

            if (localUpdatedFromRemote) {
                saveLocalReadState();
                refreshReadUI();
            }

            if (remoteNeedsUpdate) {
                const payload = {
                    files: {
                        "note_kenhori2_read_state.json": {
                            content: JSON.stringify({
                                version: 1,
                                updated_at: new Date().toISOString(),
                                items: readState
                            }, null, 2)
                        }
                    }
                };
                const patchResp = await fetch("https://api.github.com/gists/" + syncConfig.gistId, {
                    method: "PATCH",
                    headers: {
                        "Accept": "application/vnd.github+json",
                        "Authorization": "Bearer " + syncConfig.token,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });
                if (!patchResp.ok) throw new Error("PATCH HTTP " + patchResp.status);
            }

            const nowStr = new Date().toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
            updateSyncStatusUI("ok", "☁️ 同期済 (" + nowStr + ")");
        } catch (err) {
            console.warn("Gist sync error:", err);
            updateSyncStatusUI("err", "⚠️ オフライン (端末保存済)");
        } finally {
            syncInProgress = false;
        }
    }

    // --- UI Rendering & Decryption ---
    let currentReadFilter = "all"; // "all" | "unread" | "read"

    function unlockEncryptedElements() {
        if (!activeKey32) return;
        const encNodes = document.querySelectorAll("[data-enc]");
        encNodes.forEach(node => {
            const b64 = node.getAttribute("data-enc");
            if (!b64) return;
            try {
                const html = decryptBase64(b64, activeKey32);
                node.innerHTML = html;
                node.removeAttribute("data-enc");
            } catch (e) {
                console.error("Decryption error:", e);
            }
        });
        const lockBoxes = document.querySelectorAll(".lock-box");
        lockBoxes.forEach(b => b.remove());
    }

    function showLockScreenIfNeeded() {
        if (activeKey32) return;
        const encNodes = document.querySelectorAll("[data-enc]");
        encNodes.forEach(node => {
            if (node.querySelector(".lock-box")) return;
            node.innerHTML = `
                <div class="lock-box">
                    <h3>🔒 パスワード保護された記事</h3>
                    <p>記事本文の表示とPC・スマホ間の既読同期を行うにはパスワードを入力してください。<br>（一度入力するとこのブラウザに記憶されます）</p>
                    <form class="pw-form" onsubmit="return window.__noteSubmitPw(event)">
                        <input type="password" class="pw-input" placeholder="パスワードを入力..." required>
                        <button type="submit" class="pw-submit">解除</button>
                    </form>
                </div>
            `;
        });
    }

    window.__noteSubmitPw = function(ev) {
        ev.preventDefault();
        const form = ev.target;
        const input = form.querySelector(".pw-input");
        const pw = (input && input.value || "").trim();
        if (tryUnlockWithPassword(pw)) {
            unlockEncryptedElements();
            closeModal("pwModal");
            syncWithGist(false);
        } else {
            alert("パスワードが正しくありません。");
        }
        return false;
    };

    function refreshReadUI() {
        // 1. Index page cards
        const cards = document.querySelectorAll(".card[data-key]");
        let totalCount = cards.length;
        let readCount = 0;

        cards.forEach(card => {
            const key = card.getAttribute("data-key");
            const r = isArticleRead(key);
            if (r) readCount++;
            card.classList.toggle("is-read", r);
            card.setAttribute("data-read", r ? "1" : "0");
            const btn = card.querySelector(".check-btn");
            if (btn) {
                btn.classList.toggle("is-read", r);
                btn.innerHTML = r
                    ? '<span class="check-icon">✓</span><span>読了済</span>'
                    : '<span class="check-icon"></span><span>未読</span>';
                btn.title = r ? "クリックで未読に戻す" : "クリックで読了にする";
            }
        });

        if (totalCount > 0) {
            const unreadCount = totalCount - readCount;
            const pct = Math.round((readCount / totalCount) * 100);
            const statEl = document.getElementById("readProgressStats");
            if (statEl) {
                statEl.innerHTML = `読了: <span class="read-num">${readCount}</span> / ${totalCount}件 (${pct}%) <span class="unread-num">・ 未読: ${unreadCount}件</span>`;
            }
            const fillEl = document.getElementById("readProgressFill");
            if (fillEl) {
                fillEl.style.width = pct + "%";
            }
            const tabAll = document.getElementById("tabReadAll");
            const tabUnread = document.getElementById("tabReadUnread");
            const tabRead = document.getElementById("tabReadDone");
            if (tabAll) tabAll.textContent = `すべて (${totalCount})`;
            if (tabUnread) tabUnread.textContent = `未読のみ (${unreadCount})`;
            if (tabRead) tabRead.textContent = `読了済み (${readCount})`;

            if (typeof window.filterArticles === "function") {
                window.filterArticles();
            }
        }

        // 2. Article page buttons
        const articleMarker = document.querySelector("[data-article-key]");
        if (articleMarker) {
            const key = articleMarker.getAttribute("data-article-key");
            const r = isArticleRead(key);
            const topBtn = document.getElementById("topReadBtn");
            if (topBtn) {
                topBtn.classList.toggle("is-read", r);
                topBtn.innerHTML = r
                    ? '<span class="check-icon">✓</span><span>読了済</span>'
                    : '<span class="check-icon"></span><span>未読</span>';
            }
            const bottomBtn = document.getElementById("bottomReadBtn");
            if (bottomBtn) {
                bottomBtn.classList.toggle("is-read", r);
                bottomBtn.innerHTML = r
                    ? '✓ 読了済み（タップで未読に戻す）'
                    : '✓ この記事を「読了」にする';
            }
        }
    }

    window.setReadFilter = function(mode) {
        currentReadFilter = mode;
        document.querySelectorAll(".read-tab").forEach(t => {
            t.classList.toggle("active", t.getAttribute("data-mode") === mode);
        });
        if (typeof window.filterArticles === "function") {
            window.filterArticles();
        }
    };

    window.filterArticles = function() {
        const searchEl = document.getElementById("searchInput");
        const filterEl = document.getElementById("filterSelect");
        if (!searchEl || !filterEl) return;
        const q = searchEl.value.toLowerCase();
        const f = filterEl.value;
        const cards = document.querySelectorAll(".card");
        let visible = 0;
        cards.forEach(c => {
            const title = (c.getAttribute("data-title") || "").toLowerCase();
            const isFull = c.getAttribute("data-full") === "1";
            const src = c.getAttribute("data-source");
            const isRead = c.getAttribute("data-read") === "1";
            let show = title.includes(q);
            if (show && f === "full" && !isFull) show = false;
            if (show && f === "mem" && src !== "mem") show = false;
            if (show && f === "mag" && src !== "mag") show = false;
            if (show && currentReadFilter === "unread" && isRead) show = false;
            if (show && currentReadFilter === "read" && !isRead) show = false;
            c.style.display = show ? "flex" : "none";
            if (show) visible++;
        });
        const countBar = document.getElementById("countBar");
        if (countBar) countBar.textContent = "表示中: " + visible + "件";
    };

    window.sortArticles = function() {
        const sortEl = document.getElementById("sortSelect");
        const list = document.getElementById("articleList");
        if (!sortEl || !list) return;
        const order = sortEl.value;
        const cards = Array.from(list.querySelectorAll(".card"));
        cards.sort((a, b) => {
            if (order === "likes") {
                return (Number(b.getAttribute("data-likes")) || 0) - (Number(a.getAttribute("data-likes")) || 0);
            }
            const da = a.getAttribute("data-date") || "";
            const db = b.getAttribute("data-date") || "";
            return order === "asc" ? da.localeCompare(db) : db.localeCompare(da);
        });
        cards.forEach(c => list.appendChild(c));
    };

    window.openModal = function(id) {
        const el = document.getElementById(id);
        if (el) el.classList.add("open");
    };

    window.closeModal = function(id) {
        const el = document.getElementById(id);
        if (el) el.classList.remove("open");
    };

    window.copyShareUrl = function() {
        const inp = document.getElementById("shareUrlInput");
        if (!inp) return;
        inp.select();
        navigator.clipboard.writeText(inp.value).then(() => {
            const btn = document.getElementById("copyUrlBtn");
            if (btn) {
                const orig = btn.textContent;
                btn.textContent = "コピー完了!";
                setTimeout(() => btn.textContent = orig, 1500);
            }
        });
    };

    window.__noteToggleRead = function(key, ev) {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }
        toggleArticleRead(key);
    };

    window.__noteManualSync = function() {
        if (!activeKey32) {
            openModal("pwModal");
            return;
        }
        syncWithGist(true);
    };

    function injectModals() {
        const shareUrl = PAGES_URL + (activePassword ? ("#pw=" + encodeURIComponent(activePassword)) : "");
        const modalHtml = `
            <div class="modal-backdrop" id="qrModal" onclick="if(event.target===this)closeModal('qrModal')">
                <div class="modal-card">
                    <h3>📱 スマホで開く・チェック共有</h3>
                    <p>スマホのカメラで以下のQRコードを読み取ると、PCがついていなくても全記事の閲覧と既読チェックの自動同期ができます。<br>（スマホの「ホーム画面に追加」でアプリ化もできます）</p>
                    <div class="qr-wrap">${QR_SVG_DEFAULT}</div>
                    <div class="url-copy-row">
                        <input type="text" id="shareUrlInput" value="${shareUrl}" readonly onclick="this.select()">
                        <button class="icon-btn" id="copyUrlBtn" onclick="copyShareUrl()">URLコピー</button>
                    </div>
                    <button class="pw-submit" style="width:100%" onclick="closeModal('qrModal')">閉じる</button>
                </div>
            </div>
            <div class="modal-backdrop" id="pwModal" onclick="if(event.target===this)closeModal('pwModal')">
                <div class="modal-card">
                    <h3>🔑 パスワード入力</h3>
                    <p>記事のロック解除とクラウド既読同期のためのパスワードを入力してください。</p>
                    <form class="pw-form" style="margin-bottom:14px" onsubmit="return window.__noteSubmitPw(event)">
                        <input type="password" class="pw-input" placeholder="パスワード..." required>
                        <button type="submit" class="pw-submit">解除</button>
                    </form>
                    <button class="icon-btn" onclick="closeModal('pwModal')">キャンセル</button>
                </div>
            </div>
        `;
        const wrap = document.createElement("div");
        wrap.innerHTML = modalHtml;
        document.body.appendChild(wrap);
    }

    function init() {
        loadLocalReadState();
        const unlocked = autoResolveKey();
        if (unlocked) {
            unlockEncryptedElements();
        } else {
            showLockScreenIfNeeded();
        }
        injectModals();
        refreshReadUI();
        if (unlocked) {
            syncWithGist(false);
        } else {
            updateSyncStatusUI("err", "🔒 パスワード未入力");
        }

        document.addEventListener("visibilitychange", () => {
            if (document.visibilityState === "visible" && activeKey32) {
                loadLocalReadState();
                refreshReadUI();
                syncWithGist(false);
            }
        });
        window.addEventListener("pageshow", () => {
            loadLocalReadState();
            refreshReadUI();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
