window.onload = function (e) {
    // init で初期化。基本情報を取得。
    // https://developers.line.me/ja/reference/liff/#initialize-liff-app
        liff.init(function (data){
            getProfile();
            document.getElementById("closeButton").addEventListener('click',function(){
                liff.closeWindow()
            });
        });
    };

    function getProfile(){
        liff.getProfile().then(function (profile){
            document.getElementById('userIdField').textContent=profile.userId;
        });
    };
    

