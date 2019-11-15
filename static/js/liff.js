window.onload = function initializeLiff(myLiffId) {
    liff
        .init({
            liffId: myLiffId
        })
        .then(() => {
            // start to use LIFF's api
            initializeApp();
        })
        .catch((err) => {
            document.getElementById("liffAppContent").classList.add('hidden');
            document.getElementById("liffInitErrorMessage").classList.remove('hidden');
        });
}

// document.getElementById('getProfileButton').addEventListener('click', function() {
//     liff.getProfile().then(function(profile) {
//         document.getElementById('userIdProfileField').textContent = profile.userId;
//         document.getElementById('displayNameField').textContent = profile.displayName;

//         const profilePictureDiv = document.getElementById('profilePictureDiv');
//         if (profilePictureDiv.firstElementChild) {
//             profilePictureDiv.removeChild(profilePictureDiv.firstElementChild);
//         }
//         const img = document.createElement('img');
//         img.src = profile.pictureUrl;
//         img.alt = 'Profile Picture';
//         profilePictureDiv.appendChild(img);

//         document.getElementById('statusMessageField').textContent = profile.statusMessage;
//         toggleProfileData();
//     }).catch(function(error) {
//         window.alert('Error getting profile: ' + error);
//     });
// });