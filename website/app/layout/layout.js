function LayoutController($scope, $translate, $translatePartialLoader) {
    $translatePartialLoader.addPart('layout');

    $scope.changeLanguage = function (key) {
        $translate.use(key);
    };
}
