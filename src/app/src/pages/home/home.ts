import {Component} from "@angular/core";
import {NavController, Platform} from "ionic-angular";
import {Observable} from "rxjs";
import {Http} from "@angular/http";
import {iChargerService} from "../../services/icharger.service";
import {NgRedux, select} from "@angular-redux/store";
import {IAppState} from "../../models/state/configure";
import {Channel} from "../../models/channel";
import {ConfigPage} from "../config/config-page";
import {UIActions} from "../../models/state/actions/ui";
import {SystemSettingsPage} from "../system-settings/system-settings";
import {SystemActions} from "../../models/state/actions/system";
import {Subject} from "rxjs/Subject";
import {PresetListPage} from "../preset-list/preset-list";
import {ConfigStoreProvider} from "../../providers/config-store/config-store";

@Component({
    selector: 'page-home',
    templateUrl: 'home.html'
})
export class HomePage {
    @select('ui.exception') exception$: Observable<any>;
    @select() charger$: Observable<Channel>;
    @select() system$: Observable<Channel>;

    timeoutUp: boolean;
    showConfigureButton: boolean;

    private ngUnsubscribe: Subject<void> = new Subject<void>();

    ngOnDestroy() {
        this.ngUnsubscribe.next();
        this.ngUnsubscribe.complete();
    }

    constructor(public readonly navCtrl: NavController,
                public readonly chargerService: iChargerService,
                private configStore: ConfigStoreProvider,
                private uiAction: UIActions,
                private platform: Platform,
                private systemActions: SystemActions,
                public readonly ngRedux: NgRedux<IAppState>,
                public readonly http: Http) {

        let timeout = 2000;
        this.timeoutUp = false;
        this.showConfigureButton = false;

        Observable.timer(timeout)
            .takeUntil(this.ngUnsubscribe)
            .subscribe(r => {
                this.timeoutUp = true;
            });

        Observable.timer(timeout * 2)
            .takeUntil(this.ngUnsubscribe)
            .subscribe(r => {
                this.showConfigureButton = true;
            });

        // Gotta be a better way than this.
        // This takes the 2nd notification.
        // 1st I think is the store initializing.
        // 2nd is it being loaded.
        // After THAT it's OK to do stuff.
        // Pretty messy having to have empty next + error handlers
        this.ngRedux.select('config').takeUntil(this.ngUnsubscribe).take(2).subscribe(undefined, undefined, () => {
            console.log("Configuration loaded. Now getting system.");

            // Wait until configuration is loaded before starting things.
            this.platform.ready().then((r) => {
                this.systemActions.fetchSystemFromCharger();
            });

            this.loadFirstPageDoingDebugging();
        });
    }

    anyNetworkOrConnectivityProblems() {
        return this.chargerService.anyNetworkOrConnectivityProblems();
    }

    isNetworkAvailable(): boolean {
        return this.chargerService.isNetworkAvailable();
    }

    isConnectedToServer() {
        return this.chargerService.isConnectedToServer();
    }

    isConnectedToCharger() {
        return this.chargerService.isConnectedToCharger();
    }

    ionViewWillEnter() {
    }

    loadFirstPageDoingDebugging() {
        // this.showConfigPage();
        // this.showSystemPage();
        // this.showPresetsPage();
    }

    showPresetsPage() {
        this.navCtrl.push(PresetListPage);
    }

    showConfigPage() {
        this.navCtrl.push(ConfigPage);
    }

    showSystemPage() {
        this.navCtrl.push(SystemSettingsPage);
    }

    makeError() {
        this.uiAction.setErrorMessage("BOOM");
        this.uiAction.setDisconnected();
    }

    chargerText() {
        if (this.isConnectedToCharger()) {
            return "Charger OK!";
        }
        return "Can't see the charger";
    }

    serverText() {
        if (this.isConnectedToServer()) {
            return "Server/Pi connection is good!";
        }
        return "Can't see the Pi";
    }

    tips() {
        let tips = [];
        if (!this.isNetworkAvailable()) {
            tips.push("Is Wifi on? There doesn't seem to be a network.");
        }
        if (!this.isConnectedToServer()) {
            tips.push("Check that you have the correct host URL in your Configuration.");
            tips.push("Do you have network connectivity to the Pi?");
        }
        if (!this.isConnectedToCharger()) {
            tips.push("Is the charger on?");
            tips.push("Is the charger USB plugged into the Pi?");
        }
        return tips;
    }
}
